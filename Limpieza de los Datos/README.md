# **Limpieza y Arreglo de la Base de Datos NNA**

La primera etapa consistió en identificar los tipos de datos presentes en la base, junto con su volumen total de registros y columnas, equivalentes al número de variables disponibles. Se determinó que la base contiene **56.473 registros y 115 variables**.

**Tipos de datos identificados:**

- `object`: 90  
- `int64`: 21  
- `float64`: 3  
- `datetime64[ns]`: 1  

---

## **Primera Fase: Comportamiento de los Datos Faltantes**

Una vez clasificados los tipos de datos, se procedió a detectar y tratar los valores faltantes. En esta base, los datos ausentes estaban codificados como **“99999”** o **“N/A”**, los cuales fueron reemplazados por el valor estándar **`NaN`**.  
Posteriormente, se analizó el porcentaje de valores faltantes por variable. Dada la extensión de la base (115 variables), se dividieron en tres grupos según su nivel de criticidad, con el fin de definir estrategias adecuadas de tratamiento.

- **Primer grupo (0 % - 40 % de faltantes):** Variables con baja afectación.  
  📁 *Imagen ubicada en la carpeta:* `Limpieza de los Datos/Imagenes/Limpieza_Grafica1`

- **Segundo grupo (40 % - 90 % de faltantes):** Variables con afectación media.  
  📁 *Imagen ubicada en la carpeta:* `Limpieza de los Datos/Imagenes/Limpieza_Grafica2`

- **Tercer grupo (> 90 % de faltantes):** Variables críticas, registradas en una tabla independiente.  
  📁 *Tabla ubicada en:* `Limpieza de los Datos/Tablas/Tabla_Faltantes_Mayores_90%`

---

## **Segunda Fase: Limpieza, Eliminación y Transformación de Variables**

Identificadas las variables más afectadas, se evaluó su contenido y relevancia analítica. Con base en esta revisión, se decidió su **eliminación o tratamiento**, priorizando la conservación de aquellas con potencial para análisis posteriores.

Las principales razones para eliminar variables fueron:

- Ausencia total de datos.  
- Baja frecuencia de casos (por ejemplo, la variable **VEREDA**).  
- Irrelevancia analítica (**Correo 1**, **Correo 2**, **ESPECIAL**, **NÚMERO DE FICHA ANTERIOR**, **FECHA DE LA ÚLTIMA INTERVENCIÓN**, **TELÉFONO 2**, **FECHA.1**, **DIRECCIÓN DEL TRABAJO**, **.INFORMACIÓN DEL MENOR.**, entre otras).  
- Información insuficiente para imputación (**IdNivelEducativo**, **RazonAbandonoEscolar**, **SUBGRUPO SISBEN**, **PUEBLO**, **ETAPA DE GESTACIÓN**, **CLASIFICACIÓN NUTRICIONAL**, **TALLA_CM**, **PESO**, **REQUIERE ASESORÍA DE NUTRICIÓN**).  
- Variables con registros escasos vinculadas al seguimiento de casos (**ALERTAS EN MUJERES**, **ALERTAS EN NUTRICIÓN**, **ALERTAS PSICOSOCIALES**, **IEC**, **PERFIL**, **TEMAS TRATADOS**, **CONDICIONES CRÓNICAS**, **ENFERMEDADES TRANSMISIBLES Y ETV**, **ALERTAS SALUD BUCAL**, **ALERTAS INFANCIA**, **ACOMPAÑAMIENTO**, entre otras).

---

### **Transformaciones aplicadas**

1. **Unificación de variables duplicadas:**  
   Las variables **TIPO_INTERVENCION** y **TIPO INTERVENCIÓN** fueron consolidadas, manteniendo la más completa. Se unificaron categorías y registros válidos, eliminando duplicados.

2. **Cálculo de edad:**  
   Se completó la variable **EDAD** utilizando la diferencia entre **Fecha_intervencion** y **FECHA DE NACIMIENTO**, obteniendo la edad del NNA al momento del registro.

3. **Clasificación del Curso de Vida:**  
   A partir de la variable **EDAD**, se asignaron categorías correspondientes al **Curso de Vida**, completando los registros faltantes.  
   Se identificaron **11.178 casos sin datos en EDAD ni en Curso de Vida**, los cuales podrán ser considerados para depuración posterior.

4. **Estandarización de Red_fic:**  
   Se reemplazaron los códigos numéricos (1 a 4) por las denominaciones geográficas correctas: **Centro Oriente, Sur, Norte y Suroccidente**.

---

## **Tercera Fase: Segunda Depuración y Resumen de Variables Restantes**

Tras las transformaciones, se realizó una última depuración para eliminar variables redundantes o con escaso valor analítico:

- `.INFORMACIÓN DEL MENOR.` → No aporta información relevante.  
- `HABLA ESPAÑOL` → Poca variabilidad y escasa relevancia analítica.  
- `TELÉFONO 1` → Información de contacto no útil para análisis estadístico.

---

## **Variables Restantes y su Descripción**

1. **Id_fic**  
   Identificador único de cada ficha de intervención.

2. **Base_Origen**  
   Indica el periodo o fuente de captura de los datos.

3. **Ficha_fic**  
   Identificador numérico extendido asociado a cada ficha.

4. **Fecha_intervencion**  
   Abarca registros desde 2021 hasta 2025, mostrando la continuidad del programa en el tiempo.

5. **Localidad_fic**  
   Registra la localidad donde se realizó la intervención; destacan Ciudad Bolívar, Bosa y Kennedy.

6. **Red_fic**  
   Identifica la red operativa o zona de cobertura del programa.

7. **Usuario**  
   Representa al funcionario o agente de campo que diligenció la ficha.

8. **TIPO INTERVENCIÓN**  
   Clasifica el tipo de atención; predominan intervenciones con NNA (65 %) y seguimientos (23 %).

9. **NACIONALIDAD**  
   Muestra el país de origen: colombianos (83 %) y venezolanos (17 %).

10. **SEXO**  
    Distribución equilibrada entre hombres (51 %) y mujeres (49 %).

11. **GENERO**  
    Expresa identidad de género; presenta 36 % de datos faltantes.

12. **ESTADO CIVIL**  
    Predomina la categoría “No aplica” (84 %), coherente con la población infantil.

13. **FECHA DE NACIMIENTO**  
    Permite estimar la edad; registros entre 2000 y 2025.

14. **EDAD**  
    Variable numérica con promedio de 9 años (0 a 21).

15. **CURSO DE VIDA**  
    Clasifica por ciclo vital: infancia (29 %) y adolescencia (23 %).

16. **ETNIA**  
    El 99.3 % no se autorreconoce dentro de un grupo étnico.

17. **POBLACIÓN DIFERENCIAL Y DE INCLUSIÓN**  
    Predomina “No aplica” (91 %), con presencia de migrantes y personas con discapacidad.

18. **OCUPACIÓN**  
    El 62 % son estudiantes y un 27 % trabaja en el sector informal.

19. **CATEGORÍAS DE LA DISCAPACIDAD**  
    El 99.7 % sin discapacidad registrada; predominan las cognitivas (0.19 %).

20. **VÍNCULO CON EL JEFE DE HOGAR**  
    El 89 % son hijos(as) del jefe del hogar; evidencia estructuras familiares extensas.

21. **NOMBRE EAPB**  
    Mayor presencia en EPS públicas o subsidiadas; 26 % sin registro.

22. **ZONA**  
    El 99.9 % pertenece a zona urbana; mínima ruralidad.

23. **LOCALIDAD**  
    Principales localidades: Ciudad Bolívar, Bosa y Kennedy (34 % del total).

24. **UPZ/UPR**  
    Amplia cobertura territorial con promedio de 60.7 unidades.

25. **BARRIO**  
    Mayor frecuencia en Santa Fe, Santa Inés y Lisboa.

26. **BARRIO PRIORIZADO**  
    78 % sin información; predominan barrios no priorizados.

27. **MANZANA DEL CUIDADO**  
    Solo el 9 % se ubica en zonas con Manzanas del Cuidado.

28. **ESTRATO**  
    El 98 % pertenece a estratos bajos (1, 2 y 3); estrato 2 es el más común.

29. **AFILIACIÓN AL SGSSS.1**  
    Predomina régimen subsidiado (44.6 %), seguido del contributivo (39.2 %).

30. **NOMBRE EAPB.1**  
    Reitera afiliaciones en Capital Salud y Famisanar; 26 % sin información.

---

## **Variables Numéricas con Análisis Descriptivo**

1. **ESTRATO SOCIOECONÓMICO** – Estrato 2 (65 %) y 3 (20 %) predominan, reflejando niveles socioeconómicos bajos.   
2. **ZONA.1** – 99.9 % urbana, confirmando cobertura citadina.  
3. **LOCALIDAD.1** – Ciudad Bolívar, Bosa y Kennedy agrupan el 36 %.  
4. **UPZ/UPR.1** – Promedio de 60.7 unidades territoriales, alta dispersión geográfica.  
5. **BARRIO.1** – Mayor frecuencia en Santa Inés, Santa Fe y Restrepo.  
6. **BARRIO PRIORIZADO.1** – 23 % pertenece a barrios priorizados.  
7. **MANZANA DEL CUIDADO.1** – 10 % vinculados a Manzanas del Cuidado.  
8. **NOMBRE DE LA UT** – Principales tipos: hogar, reciclaje y comercio informal.  
9. **¿EN DÓNDE REALIZA PRINCIPALMENTE SU TRABAJO?** – 73 % en Unidades de Trabajo Informal.  
10. **FECHA SEGUIMIENTO** – Mayor actividad entre 2022 y 2023.  
11. **INTERVENCIÓN DE NNA QUE TERMINA EL PROCESO** – 84 % culminó el proceso.  
12. **FECHA - SEGUIMIENTO CIERRE** – Fechas de 2020 a 2025.  
13. **NNA DESVINCULADO DE LA ACTIVIDAD LABORAL** – 79 % desvinculados efectivamente.  
14. **ADOLESCENTE TRABAJO PROTEGIDO** – 98 % no aplica o no vinculado.  
