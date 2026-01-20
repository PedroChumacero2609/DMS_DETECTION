# Análisis de Distancia Mínima de Seguridad (DMS)

Este proyecto, llamado **DMS-Detection**, está diseñado para el análisis y extracción de postes de media tensión (MT) a partir de nubes de puntos etiquetadas, clasificación de postes, fusión de conexiones eléctricas y detección de colisiones, con el objetivo de generar reportes y visualizaciones detalladas del entorno y la infraestructura eléctrica.

El sistema implementa un **flujo completo y reproducible**, donde todos los módulos comparten parámetros y rutas a través del archivo `config.json`, garantizando consistencia entre reconstrucción, visualización y detección de colisiones.

---

## 📁 Configuración Global (`config.json`)

El archivo `config.json` centraliza:
- Rutas de entrada y salida
- Parámetros de visualización
- Parámetros geométricos (radio de tubo, resolución, colores)
- Rutas de CSV y JSON intermedios

Todos los módulos lo utilizan como **fuente única de verdad**.

---

## 1️⃣ Módulo Extractor

**Ubicación:** `dms_detection/extractor/`

### Estructura
```
extractor/
├─ base_extractor.py
├─ interface.py
└─ clustering/
   └─ dbscan_method.py
```

### Función
Extrae los postes de media tensión (MT) desde una nube de puntos `.PLY` etiquetada y genera archivos `.PLY` individuales por poste.

### Ejecución
```bash
python -m extractor.base_extractor
```

### Salida
```
output/poles_MT/
```

### Método por defecto
- **DBSCAN** para clustering espacial de postes

---

## 2️⃣ Módulo Clasificador

**Ubicación:** `dms_detection/classifier/`

### Estructura
```
classifier/
├─ base_classifier.py
├─ interface.py
├─ geometry_methods/
│  └─ default_geom.py
└─ models/
   └─ pointnet/
```

### Función
Clasifica cada poste como **Monoposte** o **Biposte**, calcula su geometría y exporta un CSV estructurado.

### Ejecución
```bash
python -m classifier.base_classifier
```

### Salida
```
output/poles_MT_info_classified.csv
```

### Notas clave
- La **altura real de cada poste** proviene del CSV
- Se conserva la geometría individual por poste

---

## 3️⃣ Módulo Fusión

**Ubicación:** `dms_detection/fusion/`

### Función
Genera las conexiones eléctricas entre postes MT clasificados.

### Ejecución
```bash
python -m fusion.base_fusion --mode automatic
python -m fusion.base_fusion --mode manual
```

### Salidas
- `connections.json`
- `connections.png`

### Métodos
- Automático (MST + cercanía)
- Manual (interfaz interactiva)

---

## 4️⃣ Módulo Rebuild

**Ubicación:** `dms_detection/rebuild/`

### Función
Reconstrucción visual 3D de postes MT (monoposte y biposte).

### Ejecución
```bash
python -m rebuild.rebuild_poles_MT
```

### Notas importantes
- Se utiliza **altura uniforme promedio** para visualización consistente
- Tecla **S** permite guardar capturas

---

## 5️⃣ Módulo DMS (Detección de Colisiones)

**Ubicación:** `dms_detection/DMS/`

### Archivos
```
dms/
├─ tube.py
└─ split.py
```

### Función
Detecta colisiones usando tubos envolventes y extrae el entorno relevante.

### Construcción del tubo
```bash
python -m dms.tube --radius 4
```

- El radio se propaga automáticamente a todo el pipeline
- Se generan **3 tubos por tramo** (uno por cruceta)

### Extracción de colisiones
```bash
python -m dms.split
```

### Comportamiento visual
- 🔴 Si **al menos uno de los 3 tubos** detecta colisión → **los 3 se pintan de rojo**
- 🟡 Si **ningún tubo detecta colisión** → los 3 se pintan de amarillo

### Salida
```
output/collisions/
├─ collision_report.json
├─ collision_extract_1.ply
├─ collision_extract_2.ply
...
```

---

## 6️⃣ Módulo Main (`main.py`)

**Ubicación:** raíz del proyecto

### Función
Ejecuta **todo el pipeline DMS-Detection de forma continua**, desde la extracción hasta la detección de colisiones.

### Ejecución
```bash
python main.py --mode automatic --radius 4 -i data/input.ply -o output
```

### Parámetros
- `--mode`: automatic | manual
- `--radius`: radio del tubo DMS
- `-i / --input`: PLY etiquetado de entrada
- `-o / --output`: carpeta de salida

### Flujo
1. Extractor
2. Clasificador
3. Fusión
4. Rebuild
5. DMS (tube + split)

---

## 📦 Estructura final del proyecto
```
dms_detection/
├─ extractor/
├─ classifier/
├─ fusion/
├─ rebuild/
├─ DMS/
├─ config.json
└─ main.py
```

