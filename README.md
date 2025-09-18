# Enhanced SoundCloud Downloader (yt-dlp)

**Versión 2.0 - Mejorado con yt-dlp**

---

## Descripción

Enhanced SoundCloud Downloader es una aplicación GUI avanzada para descargar audio de alta calidad desde SoundCloud y múltiples plataformas compatibles con yt-dlp. Esta herramienta ofrece una experiencia optimizada, con opciones de configuración flexibles, descarga de carátulas, organización automática por artista y progreso detallado en tiempo real.

---

## Características principales

- Descarga de audio en alta calidad desde SoundCloud y otras plataformas soportadas por yt-dlp.
- Soporte para formatos populares: MP3, M4A, FLAC y WAV.
- Selección de calidad de audio configurable (320, 256, 192, 128, 96 kbps).
- Descarga automática y embebido de carátulas en los archivos de audio.
- Opción para guardar carátulas como archivos separados (JPG o PNG).
- Organización inteligente de archivos en carpetas por artista.
- Opción para omitir archivos ya descargados y evitar duplicados.
- Interfaz gráfica moderna, intuitiva y responsiva con pestañas para descarga, configuración e información.
- Registro detallado de progreso y eventos con log integrado.
- Configuración persistente guardada en archivo JSON.
- Soporte multiplataforma: Windows, macOS y Linux.

---

## Requisitos

- Python 3.7+
- yt-dlp (instalable vía `pip install yt-dlp`)
- FFmpeg (para conversión y procesamiento de audio)
- tkinter (incluido en la mayoría de distribuciones de Python)

---

## Instalación

1. Clona o descarga este repositorio.

2. Instala las dependencias necesarias:

   pip install yt-dlp

3. Asegúrate de tener FFmpeg instalado y accesible desde la línea de comandos.

   - En Windows, puedes descargarlo desde https://www.gyan.dev/ffmpeg/builds/
   - En macOS, usa Homebrew: `brew install ffmpeg`
   - En Linux, instala desde el gestor de paquetes de tu distribución.

---

## Uso Detallado

Ejecuta la aplicación con:

   python soundcloud_downloader_improved.py

### Interfaz de Usuario

La aplicación está dividida en tres pestañas principales para facilitar la navegación y configuración:

1. Pestaña Descarga

   - Campo URL de Audio: Ingresa o pega la URL del audio que deseas descargar. Puedes usar el botón "Pegar" para obtener la URL directamente desde el portapapeles.
   - Selección de Formato y Calidad: Elige el formato de audio deseado (mp3, m4a, flac, wav) y la calidad (bitrate) entre las opciones disponibles (320, 256, 192, 128, 96 kbps).
   - Configuración de Descarga:
     - Carpeta de salida: Define la carpeta donde se guardarán los archivos descargados. Puedes explorar y seleccionar la carpeta con el botón "Explorar".
     - Crear carpetas por artista: Si está activado, la aplicación creará subcarpetas con el nombre del artista para organizar mejor los archivos.
     - Omitir archivos existentes: Evita descargar archivos que ya estén presentes en la carpeta de salida.
     - Guardar carátula separada: Permite guardar la carátula del álbum o track como un archivo independiente en formato JPG o PNG.
   - Controles:
     - Descargar: Inicia la descarga con las opciones configuradas.
     - Cancelar: Permite detener la descarga en curso.
     - Abrir carpeta: Abre la carpeta de salida en el explorador de archivos.
     - Limpiar log: Borra el registro de eventos mostrado en la interfaz.
   - Información del Track: Muestra detalles extraídos del audio, como título, artista y duración.
   - Progreso de Descarga: Barra de progreso con porcentaje, velocidad, bytes descargados y tiempo estimado restante.
   - Log Integrado: Registro en tiempo real de eventos, errores y estados de la descarga.

2. Pestaña Configuración

   - Formato y Calidad por defecto: Selecciona el formato y bitrate que se usarán automáticamente.
   - Organización de Archivos: Activa o desactiva la creación automática de carpetas por artista y la omisión de archivos existentes.
   - Configuración de Carátulas: Decide si se guardan carátulas separadas y en qué formato (jpg, png, webp).
   - Acciones:
     - Guardar configuración: Guarda los ajustes actuales en un archivo JSON para persistencia.
     - Restaurar valores por defecto: Restaura todas las opciones a sus valores originales.
     - Abrir carpeta de configuración: Abre la carpeta donde se guarda el archivo de configuración.

3. Pestaña Acerca de

   - Información sobre la aplicación, incluyendo:
     - Nombre y versión.
     - Lista de características destacadas.
     - Requisitos para su correcto funcionamiento.
     - Créditos y agradecimientos.

---

## Funcionamiento Interno

### Descarga y Procesamiento

- La descarga se ejecuta en un hilo separado para mantener la interfaz responsiva.
- Se utiliza yt-dlp para extraer información y descargar el audio.
- Antes de descargar, se extrae la información del track para mostrar detalles y organizar archivos.
- Si está activada la opción, se crea una carpeta con el nombre del artista para guardar el archivo.
- El archivo se descarga con la plantilla de nombre configurada, que puede incluir artista y título.
- Se aplican postprocesos con FFmpeg para convertir el audio al formato y bitrate seleccionados, embebiendo metadatos y carátulas.
- La carátula puede ser embebida en el archivo o guardada como archivo separado según la configuración.
- La descarga puede ser cancelada en cualquier momento, con manejo adecuado de errores y notificaciones.

### Actualización de Progreso

- La aplicación recibe actualizaciones de progreso a través de una cola desde el hilo de descarga.
- Se muestra porcentaje, velocidad, bytes descargados y tiempo estimado en la interfaz.
- El log integrado muestra mensajes de estado, errores y eventos importantes.
- Al finalizar, se notifica al usuario con un mensaje emergente y se actualiza el estado de la interfaz.

### Configuración Persistente

- Las preferencias se guardan en un archivo JSON (`downloader_config.json`) en la carpeta del usuario.
- Al iniciar, la aplicación carga esta configuración para mantener las opciones entre sesiones.
- El usuario puede modificar y guardar la configuración desde la pestaña correspondiente.

---

## Personalización Avanzada

- Plantilla de nombre de archivo: Puedes modificar la plantilla para nombrar los archivos descargados, usando campos como `%(artist)s`, `%(title)s`, etc.
- Soporte para múltiples formatos: Cambia fácilmente el formato de salida y la calidad para adaptarse a tus necesidades.
- Carpetas por artista: Organiza automáticamente tus descargas en subcarpetas para mantener tu biblioteca ordenada.
- Carátulas: Decide si quieres que las carátulas se embeban en el archivo o se guarden como archivos separados para uso externo.

---

## Solución de Problemas Comunes

- Error: yt-dlp no está instalado

  Asegúrate de instalar la dependencia con:

  pip install yt-dlp

- FFmpeg no encontrado

  Verifica que FFmpeg esté instalado y accesible desde la línea de comandos. Añade su ruta al PATH si es necesario.

- Descarga cancelada inesperadamente

  Puede ocurrir si se pierde la conexión o si el usuario cancela manualmente. Revisa el log para más detalles.

- Archivos no se guardan en la carpeta correcta

  Verifica que la carpeta de salida exista y que tengas permisos de escritura.

---

## Agradecimientos

Gracias a kanye west por salvar mi vida

---

## Contacto

Para dudas, sugerencias o soporte, puedes contactarme en:

- Email: ryverz.alonso@gmail.com
- GitHub: https://github.com/spooky1703

---

Si necesitas que te ayude con algo más, no dudes en decírmelo.
