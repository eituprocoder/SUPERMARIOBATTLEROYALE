# Local Web Builder 🤩

Servidor web local para crear y compartir sitios HTML dentro de la misma red.

## Qué incluye

- Editor HTML manual.
- Carga de archivos `.html`/`.htm`.
- Vista previa.
- Servidor HTTP real.
- Salas con código.
- URL HTTP publicable por sala: `/site/ABC123`.
- Actualización en tiempo real por WebSocket.
- Enlace de sala compartible.
- Interfaz pensada para móvil y PC.

## Instalación

Necesitás Python 3.10+.

```bash
python -m pip install -r requirements.txt
python server.py
```

Después abrí en el dispositivo del creador:

```text
http://127.0.0.1:8080/
```

Para otros dispositivos de la misma Wi‑Fi, usá la IP LAN que imprime el servidor, por ejemplo:

```text
http://192.168.1.25:8080/
```

## Flujo

1. Crear sala.
2. Escribir HTML o cargar un `.html`.
3. Copiar la URL HTTP del sitio publicado.
4. Los demás dispositivos abren esa URL en el navegador.
5. Los cambios del creador se transmiten por WebSocket.

## Importante

Este prototipo mantiene las salas en RAM. Al cerrar `server.py`, las salas desaparecen.

La página publicada es HTML servido realmente por HTTP, no una simulación P2P.

Para Android, la siguiente etapa puede ser empaquetar el servidor Python dentro de una APK/entorno Python para que el teléfono actúe como servidor LAN.
