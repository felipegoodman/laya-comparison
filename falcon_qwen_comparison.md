# Falcon3 y Qwen 2.5 para clasificar correos

Se probaron dos modelos (`falcon3:7b` y `qwen2.5:7b`) con los mismos tres correos, en dos máquinas. Cada caso se corrió una vez, con el modelo ya cargado. La clasificación salió igual en las dos máquinas. El tiempo cambió un poco.

Un caso está bien si el área es exactamente la esperada y la revisión dice lo correcto: hace falta revisar, o no. Da igual si ese valor llega como booleano o como texto.

| | Falcon3 | Qwen 2.5 |
| --- | --- | --- |
| Casos correctos | 3 de 3 | 1 de 3 |
| Área correcta | 3 de 3 | 1 de 3 |
| Revisión correcta | 3 de 3 | 2 de 3 |

Qwen termina un poco antes. Escribe menos texto. La velocidad por cada trozo de texto es casi la misma.

## Qué se probó

| Caso | Correo | Área correcta | Revisión correcta |
| --- | --- | --- | --- |
| TC-01 | No puede entrar al sistema | TI | false |
| TC-02 | Factura F-2026-104 sin pagar | Finanzas | false |
| TC-03 | Pide cinco días de vacaciones | Recursos Humanos | false |

Las únicas áreas válidas son TI, Finanzas, Recursos Humanos, Compras, Seguridad y Revisión manual.

| | Máquina de 8 GB | Máquina de 16 GB |
| --- | --- | --- |
| Memoria | 8 GB, tope de swap 8 GB | 16 GB, tope de swap 16 GB |
| Procesador | 4 núcleos | sin límite indicado |
| Modelo en memoria | se descarga al rato | se mantiene 24 horas |

## Qué respondió cada uno

La frase es el resumen del correo. Los dos la escribieron en español y sin inventar datos. Esta tabla vale para las dos máquinas.

| Caso | Falcon3 | Qwen 2.5 | Resultado |
| --- | --- | --- | --- |
| TC-01 | Área **TI**, revisión false. «Acceso al sistema rechazado» | Área **TI**, revisión false. «Problema de acceso al sistema corporativo» | Los dos bien |
| TC-02 | Área **Finanzas**, revisión false. «Consulta sobre estado de factura F-2026-104» | Área **Facturación**, revisión false. «Consulta sobre estado y fecha de pago de factura» | Falcon bien. Qwen acierta la revisión y falla el área |
| TC-03 | Área **Recursos Humanos**, revisión false. «Solicitud de vacaciones» | Área **Revisión manual**, revisión true. «Solicitud de vacaciones - procedimiento y disponibilidad» | Falcon bien. Qwen falla área y revisión |

Qwen entiende de qué trata el correo. En el acceso al sistema lo deja bien. En la factura dice que no hace falta revisión, que es correcto, pero el nombre del área no está en la lista: tenía que ser Finanzas. En las vacaciones lo manda a revisión aunque el pedido es claro.

## Cómo leer los tiempos

Cada respuesta se parte en dos tramos:

| Medida | En las notas | Qué es, en corto |
| --- | --- | --- |
| Lectura | `tiempo_eval_prompt_seg` | Segundos para leer las instrucciones y el correo |
| Escritura | `tiempo_generacion_seg` | Segundos para redactar el JSON |
| Total | `tiempo_total_seg` | Lectura más escritura |
| Tokens | `tokens_generados` | Cuánto texto escribió. Cuenta todo el JSON, no solo la frase |
| Velocidad | `velocidad_tokens_por_seg` | Tokens por segundo durante la escritura |

Un token es un trozo de palabra. Quien escribe menos tokens puede terminar antes aunque no escriba más rápido. Por eso la velocidad importa tanto como el reloj total.

La carga del modelo fue 0 segundos en todas las pruebas: ya estaba en memoria.

## Máquina de 8 GB

| Caso | Modelo | Lectura (s) | Escritura (s) | Total (s) | Tokens | Velocidad (tok/s) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| TC-01 | Falcon3 | 8.09 | 10.28 | 18.38 | 52 | 5.06 |
| TC-01 | Qwen 2.5 | 9.66 | 10.07 | 19.74 | 46 | 4.57 |
| TC-02 | Falcon3 | 9.38 | 11.91 | 21.30 | 64 | 5.37 |
| TC-02 | Qwen 2.5 | 7.51 | 8.43 | 15.95 | 50 | 5.93 |
| TC-03 | Falcon3 | 8.34 | 9.75 | 18.09 | 54 | 5.54 |
| TC-03 | Qwen 2.5 | 8.57 | 10.43 | 19.01 | 51 | 4.89 |
| **Media** | **Falcon3** | **8.60** | **10.65** | **19.26** | **56.7** | **5.32** |
| **Media** | **Qwen 2.5** | **8.58** | **9.64** | **18.23** | **49.0** | **5.13** |

En esta máquina la lectura queda empatada. Qwen escribe menos (147 tokens en los tres correos, Falcon 170) y por eso su escritura y su total bajan. Por token, Falcon va un poco más rápido: 5.32 frente a 5.13.

El caso de la factura es el que más inclina el total. Falcon escribe 64 tokens y tarda 11.91 s en redactar. Qwen escribe 50 y tarda 8.43 s. Ahí Qwen también va más rápido por token (5.93 frente a 5.37). En los otros dos correos, Falcon es más rápido por token.

## Máquina de 16 GB

Los tokens no cambian: la respuesta escrita es la misma. Cambia el reloj.

| Caso | Modelo | Lectura (s) | Escritura (s) | Total (s) | Tokens | Velocidad (tok/s) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| TC-01 | Falcon3 | 8.52 | 9.13 | 17.65 | 52 | 5.70 |
| TC-01 | Qwen 2.5 | 8.05 | 8.31 | 16.37 | 46 | 5.54 |
| TC-02 | Falcon3 | 8.53 | 11.42 | 19.95 | 64 | 5.61 |
| TC-02 | Qwen 2.5 | 8.90 | 8.88 | 17.80 | 50 | 5.63 |
| TC-03 | Falcon3 | 8.12 | 9.62 | 17.74 | 54 | 5.62 |
| TC-03 | Qwen 2.5 | 8.38 | 9.18 | 17.56 | 51 | 5.56 |
| **Media** | **Falcon3** | **8.39** | **10.06** | **18.45** | **56.7** | **5.64** |
| **Media** | **Qwen 2.5** | **8.44** | **8.79** | **17.24** | **49.0** | **5.58** |

La lectura sigue empatada, alrededor de 8.4 s. La velocidad también: 5.64 frente a 5.58 tokens por segundo. Qwen acaba la escritura antes porque genera 23 tokens menos en el conjunto, no porque escriba mucho más rápido.

En la factura, los dos van a 5.6 tokens por segundo. Falcon tarda 11.42 s porque escribe 64 tokens. Qwen tarda 8.88 s porque escribe 50.

## Las dos máquinas, juntas

| Medida | Falcon3, 8 GB | Qwen 2.5, 8 GB | Falcon3, 16 GB | Qwen 2.5, 16 GB |
| --- | ---: | ---: | ---: | ---: |
| Casos correctos | 3/3 | 1/3 | 3/3 | 1/3 |
| Lectura media (s) | 8.60 | 8.58 | 8.39 | 8.44 |
| Escritura media (s) | 10.65 | 9.64 | 10.06 | 8.79 |
| Total medio (s) | 19.26 | 18.23 | 18.45 | 17.24 |
| Tokens medios | 56.7 | 49.0 | 56.7 | 49.0 |
| Velocidad (tok/s) | 5.32 | 5.13 | 5.64 | 5.58 |

Pasar de 8 GB a 16 GB bajó un poco los relojes y no cambió ninguna etiqueta ni ningún token.

## Conclusión

Falcon3 clasifica bien los tres correos. Qwen 2.5 resume el correo, escribe un poco menos y por eso el reloj total se ve mejor. Deja bien el acceso al sistema. En la factura acierta que no hace falta revisión, pero usa un área que no está en la lista. En las vacaciones pide revisión de más.

Para elegir modelo en este trabajo pesa más acertar el área que ganar 1 segundo. La lectura del correo es igual de lenta en los dos. La velocidad de escritura también es muy parecida, sobre todo en la máquina de 16 GB.
