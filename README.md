# Social Media Post Deleter

Este repositorio contiene dos scripts automatizados desarrollados en Python utilizando **Playwright** para eliminar publicaciones antiguas de X (Twitter) y Facebook de forma masiva y gratuita, sin necesidad de usar APIs oficiales de pago.

> [!WARNING]
> **Seguridad:** Los perfiles locales de Chrome (`x_chrome_profile` y `fb_chrome_profile`) que contienen tus sesiones activas e inicio de sesión están excluidos en el archivo `.gitignore`. **Nunca** compartas o subas estas carpetas a repositorios públicos, ya que contienen tus tokens y cookies de sesión.

---

## Características

1. **Delete Old Tweets (X.com):**
   - Navega directamente a tu perfil de X.
   - Lee el año exacto de cada tweet.
   - Si es del año 2016 en adelante, lo omite para proteger tus tweets recientes.
   - Si es del **2015 o más antiguo**, lo elimina automáticamente simulando clics reales.
   - Guarda tu sesión localmente para que no tengas que iniciar sesión cada vez.

2. **Delete Facebook Posts (Facebook):**
   - Te permite iniciar sesión manualmente.
   - Te dirige al **Registro de Actividad** de tu cuenta.
   - Tú aplicas el filtro de fecha (ej. 2015 y anteriores) y categoría.
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

### 1. Eliminar Tweets de X (2015 hacia atrás)
Ejecuta el script:
```bash
python delete_old_tweets.py
```
- Se abrirá un navegador Chromium. Si no has iniciado sesión, el script te guiará para que lo hagas manualmente.
- Una vez iniciada la sesión, presiona ENTER en la terminal. El script irá a tu perfil y borrará automáticamente los posts anteriores a 2016.

### 2. Eliminar Publicaciones de Facebook
Ejecuta el script:
```bash
python delete_fb_posts.py
```
- Se abrirá un navegador Chromium. Inicia sesión en tu cuenta de Facebook.
- Ve a tu **Registro de actividad** (`https://www.facebook.com/me/allactivity`).
- Filtra por el año (ej. 2015) y la categoría deseada de publicaciones.
- Vuelve a la terminal y presiona ENTER para iniciar la eliminación automática.
