# Social Media Post Deleter

Este repositorio contiene dos scripts automatizados desarrollados en Python utilizando **Playwright** para eliminar publicaciones antiguas de X (Twitter) y Facebook de forma masiva y gratuita, sin necesidad de usar APIs oficiales de pago.

> [!WARNING]
> **Seguridad:** Los perfiles locales de Chrome (`x_chrome_profile` y `fb_chrome_profile`) que contienen tus sesiones activas e inicio de sesión están excluidos en el archivo `.gitignore`. **Nunca** compartas o subas estas carpetas a repositorios públicos, ya que contienen tus tokens y cookies de sesión.

---

## Características

1. **Delete Old Tweets (X.com):**
   - Te solicita tu nombre de usuario y la fecha límite que elijas.
   - Navega directamente a tu perfil de X.
   - Compara las fechas de cada publicación.
   - Si la publicación es del día o fecha límite indicada y anteriores, la elimina automáticamente. Si es posterior, la conserva intacta.
   - Guarda tu sesión localmente para que no tengas que iniciar sesión cada vez.

2. **Delete Facebook Posts (Facebook):**
   - Te solicita el año límite que deseas eliminar.
   - Abre el navegador para que inicies sesión manualmente.
   - Te dirige al **Registro de Actividad** de tu cuenta y te recuerda configurar los filtros manualmente para ese año y anteriores.
   - Presionas ENTER en la consola y el script elimina o envía a la papelera todos los posts visibles de esa lista de forma secuencial.

---

## Requisitos Previos

Asegúrate de tener instalado Python en tu sistema.

1. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

2. Instala el navegador de Playwright:
   ```bash
   python -m playwright install chromium
   ```

---

## Instrucciones de Uso

### 1. Eliminar Tweets de X
Ejecuta el script:
```bash
python delete_old_tweets.py
```
- Introduce tu nombre de usuario (sin @) y la fecha límite en formato `AAAA-MM-DD` (por ejemplo, `2015-12-31` borrará todo lo publicado en esa fecha y antes de ella).
- Se abrirá un navegador Chromium. Si no has iniciado sesión, hazlo de forma manual en la ventana.
- Una vez iniciada la sesión y estando en el inicio (Home), regresa a la terminal y presiona ENTER. El script irá a tu perfil y borrará automáticamente los posts que cumplan con el filtro de fecha establecido.

### 2. Eliminar Publicaciones de Facebook
Ejecuta el script:
```bash
python delete_fb_posts.py
```
- Introduce el año límite que desees eliminar (por ejemplo, `2015`).
- Se abrirá un navegador Chromium. Inicia sesión en tu cuenta de Facebook.
- Ve al **Registro de actividad** (`https://www.facebook.com/me/allactivity`).
- Filtra por el año introducido (o el que prefieras) y la categoría deseada de publicaciones.
- Vuelve a la terminal y presiona ENTER para iniciar la eliminación automática de todo lo que esté en pantalla.

