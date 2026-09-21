"""Reconstruct SIPA records and preserve the original 232-column schema."""

import csv

from CONFIG import (
    ENCODING,
    EXPECTED_COLUMNS,
    FIELD_SIZE_LIMIT,
    FOLDED_ROWS_LOG,
    RECORD_START,
)


def parse_continuation(text, split_index, abstract_index):
    values = next(csv.reader(["," + text]))
    abstract_offset = abstract_index - split_index
    if abstract_offset >= len(values):
        return values
    if not values[abstract_offset].strip():
        return values

    end = abstract_offset
    while end + 1 < len(values) and values[end + 1].strip():
        end += 1

    return values[:abstract_offset] + [
        ",".join(values[abstract_offset : end + 1])
    ] + values[end + 1 :]


def parse_folded_rows(buffer, split_index):
    first = next(csv.reader([buffer[0]]))
    merged = first[:]
    abstract_index = 35

    for line in buffer[1:]:
        closing_quote = line.find('",')
        if closing_quote >= 0:
            author_tail = line[:closing_quote].lstrip('"')
            continuation = parse_continuation(
                line[closing_quote + 2 :], split_index, abstract_index
            )
            merged[split_index] += author_tail
            for index, value in enumerate(continuation):
                destination = split_index + index
                if destination < len(merged) and value:
                    merged[destination] = value
            break
        else:
            merged[split_index] += line.lstrip('"')

    return merged


def normalize_row(row, header):
    values = list(row[:len(header)])
    values.extend([""] * (len(header) - len(values)))
    for index, name in enumerate(header):
        if name.endswith("[]"):
            values[index] = ""

    abstract_index = header.index("dc.description.abstract")
    language_abstract_name = "dc.description.abstract[es_CL]"
    if language_abstract_name in header:
        language_abstract_index = header.index(language_abstract_name)
        if values[abstract_index] and values[language_abstract_index]:
            values[abstract_index] += " " + values[language_abstract_index]
            values[language_abstract_index] = ""

    return values


def records(input_file, folded_log):
    """Yield the header and reconstructed records from a SIPA export."""

    header = next(csv.reader([input_file.readline().rstrip("\r\n")]))
    split_index = header.index("dc.contributor.author")
    yield header

    buffer = None
    for line in input_file:
        line = line.rstrip("\r\n")
        if not line:
            continue
        if RECORD_START.match(line):
            if buffer is not None:
                folded_log.write("\n".join(buffer) + "\n\n") if len(buffer) > 1 else None
                yield parse_folded_rows(buffer, split_index)
            buffer = [line]
        elif buffer is not None:
            buffer.append(line)

    if buffer is not None:
        folded_log.write("\n".join(buffer) + "\n\n") if len(buffer) > 1 else None
        yield parse_folded_rows(buffer, split_index)


def configure_document(source):
    
    """Read the export and return its reconstructed header and rows."""
    
    csv.field_size_limit(FIELD_SIZE_LIMIT)
    
    with source.open("r", encoding=ENCODING, errors="replace", newline="") as input_file, FOLDED_ROWS_LOG.open("w", encoding=ENCODING) as folded_log:
        reader = records(input_file, folded_log)
        header = next(reader)
        
        while header and not header[-1].strip():
            header.pop()
            
        if len(header) != EXPECTED_COLUMNS:
            raise ValueError(f"Expected {EXPECTED_COLUMNS} columns, got {len(header)}")
        rows = [normalize_row(row, header) for row in reader]
        
    return header, rows
