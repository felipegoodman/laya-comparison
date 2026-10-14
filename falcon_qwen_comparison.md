# Falcon3 y Qwen 2.5: comparación de las salidas

Fuente: `notes.md`. Modelos medidos: `falcon3:7b` y `qwen2.5:7b`. El apartado de las notas se titula «QWEN 3», pero el JSON de cada respuesta trae `"modelo": "qwen2.5:7b"`, el mismo nombre del `curl` inicial. Esta comparación usa el identificador de la salida.

Casos medidos: TC-01, TC-02 y TC-03. Una corrida por caso y entorno, `temperature` 0, `format: json`, `num_predict` 80. TC-04 y TC-05 no están en las notas.

Área esperada, tomada de cada fichero de caso:

| Caso | Correo | Área esperada | `requiere_revision` esperado |
| --- | --- | --- | --- |
| TC-01 | Acceso al sistema rechazado | TI | false |
| TC-02 | Factura F-2026-104 pendiente de pago | Finanzas | false |
| TC-03 | Cinco días de vacaciones | Recursos Humanos | false |

El prompt admite solo TI, Finanzas, Recursos Humanos, Compras, Seguridad y Revisión manual. `categoria` y `area_destinataria` deben ser el mismo nombre. `requiere_revision` debe ser booleano.

## Entornos

No cambian las clasificaciones. Solo cambia un poco el tiempo.

| | Entorno 1 | Entorno 2 |
| --- | --- | --- |
| Memoria | 8 GB, swap 8 GB | 16 GB, swap 16 GB |
| CPU | `--cpus=4` | no consta límite de CPU |
| Ollama | sin `KEEP_ALIVE` ni tope de modelos | `OLLAMA_KEEP_ALIVE=24h`, `OLLAMA_MAX_LOADED_MODELS=2` |

`tiempo_carga_modelo_seg` es 0 en las doce salidas. El modelo ya estaba cargado. Estas cifras no incluyen un arranque en frío.

## Clasificación

Las dos máquinas devolvieron el mismo JSON de clasificación para cada modelo. La tabla vale para los dos entornos.

| Caso | Falcon3 | Qwen 2.5 | Esperado |
| --- | --- | --- | --- |
| TC-01 | TI, revisión `false` (booleano) | TI, revisión `"false"` (texto) | TI, false |
| TC-02 | Finanzas, revisión `false` | Facturación, revisión `"false"` (texto) | Finanzas, false |
| TC-03 | Recursos Humanos, revisión `false` | Revisión manual, revisión `true` (booleano) | Recursos Humanos, false |

Falcon acierta el área en los tres casos y devuelve el booleano `false`, como pide el caso y el prompt.

Qwen acierta el área solo en TC-01. En TC-02 elige «Facturación», que describe el tema pero no está en la lista cerrada; la etiqueta válida era Finanzas. En TC-03 manda a Revisión manual un pedido de vacaciones explícito y pone `requiere_revision` en `true`. El motivo de ese caso sí resume la solicitud («procedimiento y disponibilidad»), pero el área no corresponde.

En TC-01 y TC-02, Qwen entrega `requiere_revision` como el texto `"false"`, no como booleano. En TC-03 sí entrega un booleano. Falcon entrega booleano en los tres.

Criterio estricto: área igual a la esperada y `requiere_revision` booleano e igual al esperado.

| Criterio | Falcon3 | Qwen 2.5 |
| --- | --- | --- |
| Área correcta | 3/3 | 1/3 |
| Revisión con tipo y valor correctos | 3/3 | 0/3 |
| Caso completo | 3/3 | 0/3 |

Si se lee `"false"` como el valor falso e se ignora el tipo, Qwen acertaría la revisión en TC-01 y TC-02, y el caso completo solo en TC-01. TC-02 seguiría mal por el área. TC-03 seguiría mal por área y por revisión.

## Motivo

Los dos escriben una síntesis corta en español, por debajo de las 15 palabras pedidas, y no inventan remitentes. El texto no se puntúa contra una frase fija.

| Caso | Falcon3 | Qwen 2.5 |
| --- | --- | --- |
| TC-01 | Acceso al sistema rechazado | Problema de acceso al sistema corporativo |
| TC-02 | Consulta sobre estado de factura F-2026-104 | Consulta sobre estado y fecha de pago de factura |
| TC-03 | Solicitud de vacaciones | Solicitud de vacaciones - procedimiento y disponibilidad |

Falcon es más breve. En TC-02 conserva el identificador F-2026-104, que sí está en el correo. Qwen en TC-02 añade la fecha de pago, que el correo también pide. La diferencia útil no es el estilo del motivo: es que Falcon ata ese texto a un área permitida y Qwen, en dos casos, no.

## Tiempo

Suma de `tiempo_total_seg` de los tres casos. Una sola corrida por celda: la diferencia de unos segundos no alcanza para declarar un ganador estable de velocidad.

| | Falcon3, entorno 1 | Qwen 2.5, entorno 1 | Falcon3, entorno 2 | Qwen 2.5, entorno 2 |
| --- | ---: | ---: | ---: | ---: |
| TC-01 | 18.38 | 19.74 | 17.65 | 16.37 |
| TC-02 | 21.30 | 15.95 | 19.95 | 17.80 |
| TC-03 | 18.09 | 19.01 | 17.74 | 17.56 |
| Suma | 57.77 | 54.70 | 55.34 | 51.73 |
| Media | 19.26 | 18.23 | 18.45 | 17.24 |

En el entorno de 8 GB, Qwen es más rápido solo en TC-02 (15.95 s contra 21.30 s). Falcon es más rápido en TC-01 y TC-03. La suma favorece a Qwen por 3.07 s.

En el entorno de 16 GB, Qwen tiene menor tiempo total en los tres casos. En TC-03 la diferencia es 0.18 s. La suma favorece a Qwen por 3.61 s.

Pasar de 8 GB y 4 CPU a 16 GB con el modelo residente bajó la suma de Falcon 2.43 s (57.77 a 55.34) y la de Qwen 2.97 s (54.70 a 51.73). No cambió ninguna etiqueta.

Tokens y velocidad de generación, iguales en los dos entornos para el conteo de tokens:

| | Falcon3, tokens | Qwen 2.5, tokens | Falcon3, tok/s entorno 1 | Qwen 2.5, tok/s entorno 1 | Falcon3, tok/s entorno 2 | Qwen 2.5, tok/s entorno 2 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| TC-01 | 52 | 46 | 5.06 | 4.57 | 5.70 | 5.54 |
| TC-02 | 64 | 50 | 5.37 | 5.93 | 5.61 | 5.63 |
| TC-03 | 54 | 51 | 5.54 | 4.89 | 5.62 | 5.56 |
| Media | 56.7 | 49.0 | 5.32 | 5.13 | 5.64 | 5.58 |

La velocidad por token es parecida. Falcon genera más tokens (170 contra 147 en los tres casos), y por eso su tramo de generación suele durar más aunque los tok/s no sean peores. Evaluar el prompt ocupa alrededor de 8–9 s en ambos, una parte grande del total.

## Qué se puede concluir

En estos tres correos, Falcon3 cumple el catálogo y el tipo booleano, y asigna TI, Finanzas y Recursos Humanos como está definido en los casos. Qwen 2.5 resume bien el contenido, pero solo acierta el área en el problema de acceso, se sale del catálogo en la factura y trata las vacaciones como ambiguas. Además, en dos de tres respuestas el campo de revisión es texto, no booleano.

El tiempo total de estas corridas favorece a Qwen por unos 3–4 s en el conjunto, con el modelo ya cargado. Caso a caso no gana siempre, y no hay repeticiones para separar esa diferencia del ruido. Cambiar memoria y la permanencia del modelo en Ollama no modificó ninguna clasificación.

No se puede extender este resultado a los correos ambiguos ni al correo con instrucciones incrustadas: esas pruebas no están en las notas.
