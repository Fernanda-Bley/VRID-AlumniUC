![Portada](scr/Grupo-11-Proyecto-SIPA.png)

# VRID-AlumniUC - Branch Feña
----
## Uniendo, Estandarizando y limpiando datos

> Avances disponibles en [data-analisis](data-analisis.ipynb)

#### Uniendo los datos
Para estandarizar los datos uní todos las columnas tipo ```dc.code``` y ```dc.code[]```. Esto se hizo con la función ```combine_columns``` Esto nos permitió reducir de 232 columnas a 131. La unión se hizo con un ```;``` así podemos identificar que estaba originalmente en la columna y que fue añadido. 

Luego aplicamos ```divide_lines``` que divide todas las columnas con divisiones tipo ```||``` para así transformarlas en listas. La transformación se vería como: 

```nombre_1||nombre_2||nombre_3;nan``` -> ```[nombre_1,nombre_2,nombre_3;nan]```

#### Estandarización

Aplicamos un pipeline que limpia, estandariza y normaliza datos en una cadena de texto limpia y uniforme, o el mensaje `"No hay registro"` si no hay datos válidos.
Exploramos las columnas que necesitan división por su naturaleza: 

```
columns_to_divide = [
    "dc.contributor.author",
    "dc.contributor.advisor",
    "dc.contributor.editor",
    "dc.date.concesion",
    "dc.date.created"
]
```


Para esto:

1. **Manejo de Listas o Arrays de NumPy**

* Si el valor es una lista o un array, lo convierte a lista de Python.
* Recorre cada elemento. Si es un `NaN` de Pandas, lo ignora.
* Convierte el elemento a texto y usa una expresión regular (`re.split(r';|\|\|', s)`) para dividir el texto cada vez que encuentre un `;` o un `||`.
* Limpia los espacios de cada fragmento resultante. Si el fragmento no está vacío y no es la palabra "nan", lo guarda.
* Al final, si no quedó nada, devuelve `"No hay registro"`. Si quedó algo, une todo con `;`.

2. **Manejo de Cadenas (Strings) o Números:**

* Si es un texto o un número, lo convierte a string y le quita los espacios de los bordes.
* Si el texto es literalmente `"nan"`, devuelve `"No hay registro"`.
* Al igual que en el Bloque 1, divide el texto por `;` o `||`, filtra los espacios y los valores vacíos/nulos.
* Devuelve los fragmentos limpios unidos por `;`. Si algo falla o queda vacío, devuelve `"No hay registro"`.

3. **Manejo de NaN escalar:** Si el valor no es una lista, verifica si es un valor nulo (`NaN`, `None`, etc.). Si lo es, devuelve inmediatamente `"No hay registro"`. (El `try/except` evita que el código rompa si `val` es un tipo de dato complejo que Pandas no puede evaluar fácilmente).

```

"Tipo A || Tipo B" -> `"Tipo A;Tipo B"`
"Tipo A ; Tipo B || Tipo C"` -> "Tipo A;Tipo B;Tipo C"
["Tipo A || Tipo B", "Tipo C"] -> "Tipo A;Tipo B;Tipo C"
np.nan -> "No hay registro"
"  ;  ||  nan  " -> "No hay registro"
12345 -> "12345"
```
#### Limpieza y casos extraordinarios

Para eliminar los nan ocuparemos ```clean_nan``` la cual divide nuevamente los datos en su punto `;` para eliminar los nan y revisar casos extraordinarios que no hayan sido eliminados en la primera vuelta. 

1. **Manejar valores nulos escalares (```None, np.nan, pd.NA```)**: Si no encuentra ningún dato que no sea tipo nan (None o Strings que solo contienen la palabra "nan") entonces lo reemplaza con un "No hay registro".


2. **Manejar Listas y Arrays de NumPy**: Unifica separadores múltiples la función normaliza todo a un único separador (```;```). Esto en caso que no haya sido explorado en otras columnas. 

```
    Ejemplo: "A || B ; C" → "A;B;C"
```

3. **Manejar Strings y Números**: Si la entrada es una lista o un array de NumPy: Itera sobre cada elemento y une los elementos válidos restantes con ;.

```
    Ejemplo: ["Tipo A", np.nan, "Tipo B"] → "Tipo A;Tipo B"
```

#### Cosas por solucionar

* Datos incorrectos y sin sentido : Hay datos que son nombres propios o información incoherente (pedazos de abstract).

* DC Cargado valores adicionales extraños: pau;21-12-2022 y aba;11-01-2023 aparecen combinando estas palabras con las fechas. 



