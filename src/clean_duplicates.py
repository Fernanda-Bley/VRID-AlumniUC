"""Deduplicate records using DOI, URI, or ISBN plus title."""

import json
import re
import unicodedata
from decimal import Decimal, InvalidOperation


IDENTIFIER_FIELDS = {
	"yid",
	"dc.identifier.doi",
	"dc.identifier.uri",
	"dc.identifier.isbn",
	"dc.identifier.eisbn",
}
ISBN_FIELDS = {"dc.identifier.isbn", "dc.identifier.eisbn"}


def match_key(value):
	"""Normalize a value for comparison without changing its display form."""
	decomposed = unicodedata.normalize("NFKD", str(value).casefold())
	without_accents = "".join(
		character for character in decomposed if not unicodedata.combining(character)
	)
	return re.sub(r"[^\w]+", " ", without_accents, flags=re.UNICODE).strip()


def standardize_text(value):
	"""Normalize whitespace while preserving capitalization."""
	return " ".join(unicodedata.normalize("NFC", str(value)).split())


def standardize_delimited(value, delimiter="||"):
	"""Standardize and deduplicate a delimiter-separated display field."""
	result = []
	seen = set()
	for item in value.split(delimiter):
		standardized = standardize_text(item)
		key = match_key(standardized)
		if standardized and key not in seen:
			seen.add(key)
			result.append(standardized)
	return delimiter.join(result)


def _index(header, name):
	return header.index(name) if name in header else None


def _author_indexes(header):
	return [
		index for index, name in enumerate(header)
		if "author" in name.lower() or "autor" in name.lower()
	]


def _tokens(value, field):
	"""Split identifier cells without splitting DOI or URI punctuation."""
	delimiter = r"\|\||;|," if field in ISBN_FIELDS else r"\|\|;"
	return [token.strip() for token in re.split(delimiter, str(value)) if token.strip()]


def _doi_key(value):
	value = re.sub(
		r"^https?://(?:dx\.)?doi\.org/", "", value.strip(), flags=re.IGNORECASE
	)
	value = re.sub(r"^doi:\s*", "", value, flags=re.IGNORECASE).rstrip(".,;)")
	return value.casefold() if re.fullmatch(r"10\.\d{4,9}/\S+", value) else None


def _doi_keys_in_uri(value):
	"""Extract DOI values embedded in repository or publisher URLs."""
	return {
		key
		for candidate in re.findall(r"10\.\d{4,9}/[^\s|;]+", value, re.IGNORECASE)
		if (key := _doi_key(candidate))
	}


def _isbn_key(value):
	compact = re.sub(r"[^0-9Xx]", "", value)
	if re.fullmatch(r"\d{9}[0-9Xx]", compact) or re.fullmatch(r"\d{13}", compact):
		return compact.upper()
	try:
		number = Decimal(value.strip())
	except (InvalidOperation, ValueError):
		return None
	if number == number.to_integral_value():
		digits = str(number.quantize(Decimal("1")).to_integral_value())
		if re.fullmatch(r"\d{10}|\d{13}", digits):
			return digits
	return None


def _row_keys(header, row):
	"""Return usable keys, with ISBN restricted to rows lacking DOI and URI."""
	keys = []
	doi_index = _index(header, "dc.identifier.doi")
	has_doi = False
	if doi_index is not None:
		for value in _tokens(row[doi_index], "dc.identifier.doi"):
			doi = _doi_key(value)
			if doi:
				has_doi = True
				keys.append(("doi", doi))

	uri_index = _index(header, "dc.identifier.uri")
	has_uri = False
	if uri_index is not None:
		for value in _tokens(row[uri_index], "dc.identifier.uri"):
			if value:
				has_uri = True
				embedded_dois = _doi_keys_in_uri(value)
				if embedded_dois:
					keys.extend(("doi", doi) for doi in embedded_dois)
				else:
					keys.append(("uri", value))

	title_index = _index(header, "dc.title")
	if not has_doi and not has_uri and title_index is not None and row[title_index].strip():
		title = match_key(row[title_index])
		for field in ISBN_FIELDS:
			index = _index(header, field)
			if index is not None:
				for value in _tokens(row[index], field):
					isbn = _isbn_key(value)
					if isbn:
						keys.append(("isbn-title", isbn, title))
	return keys


def _row_quality(row):
	return sum(bool(str(value).strip()) for value in row)


def _merge_rows(header, first, second):
	"""Merge values; descriptive conflicts use ``||``, identifiers do not."""
	if len(first) != len(header) or len(second) != len(header):
		raise ValueError("Every row must have the same length as the header")
	author_indexes = set(_author_indexes(header))
	merged = []
	conflicts = []
	for index, (first_value, second_value) in enumerate(zip(first, second)):
		first_value = str(first_value)
		second_value = str(second_value)
		field = header[index]
		if not first_value.strip():
			merged.append(second_value)
		elif not second_value.strip() or match_key(first_value) == match_key(second_value):
			merged.append(first_value)
		elif field in IDENTIFIER_FIELDS or field.startswith("dc.identifier."):
			merged.append(first_value)
			conflicts.append(field)
		elif index in author_indexes or "||" in first_value or "||" in second_value:
			merged.append(standardize_delimited(f"{first_value}||{second_value}"))
		else:
			merged.append(f"{first_value}||{second_value}")
	return merged, conflicts


def _log_record(merged_row, removed_row, matched_field, conflicts):
	reason = "identifier_conflict" if conflicts else "identifier_merge"
	matched = matched_field
	if conflicts:
		matched += f"; conflicts={','.join(conflicts)}"
	return [
		merged_row[0], removed_row[0], "identifier", matched, reason,
		json.dumps(merged_row, ensure_ascii=False),
		json.dumps(removed_row, ensure_ascii=False),
	]


def deduplicate_rows(header, rows):
	"""Merge duplicate records transitively and return an audit log."""
	parent = list(range(len(rows)))
	row_keys = []
	key_to_row = {}

	def find(index):
		while parent[index] != index:
			parent[index] = parent[parent[index]]
			index = parent[index]
		return index

	def union(left, right):
		left_root, right_root = find(left), find(right)
		if left_root != right_root:
			parent[right_root] = left_root

	for row_index, row in enumerate(rows):
		if len(row) != len(header):
			raise ValueError("Every row must have the same length as the header")
		keys = _row_keys(header, row)
		row_keys.append(keys)
		for key in keys:
			if key in key_to_row:
				union(row_index, key_to_row[key])
			else:
				key_to_row[key] = row_index

	groups = {}
	for index in range(len(rows)):
		groups.setdefault(find(index), []).append(index)

	kept = []
	logs = []
	for indexes in groups.values():
		base_index = max(indexes, key=lambda index: _row_quality(rows[index]))
		merged = rows[base_index]
		for index in indexes:
			if index == base_index:
				continue
			matched = sorted({key[0] for key in row_keys[index] if key in row_keys[base_index]})
			merged, conflicts = _merge_rows(header, merged, rows[index])
			logs.append(_log_record(merged, rows[index], ",".join(matched) or "transitive_match", conflicts))
		kept.append(merged)
	return kept, logs
