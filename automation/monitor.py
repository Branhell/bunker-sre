#!/usr/bin/env python3
"""
Bunker SRE - Bot de Monitoreo
Verifica el estado de los contenedores Docker cada 30 segundos
"""

import docker
import requests
import schedule
import time
import logging
from datetime import datetime

# ── Configuración de logs ──────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('bunker_monitor.log'),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# ── Cliente Docker ─────────────────────────────────────────────
client = docker.from_env()

# ── Contenedores a monitorear ──────────────────────────────────
CONTENEDORES = ['bunker-nginx', 'bunker-postgres']
NGINX_URL = 'http://localhost:8080'

def verificar_contenedores():
    """Verifica el estado de cada contenedor"""
    log.info("=" * 50)
    log.info("Iniciando verificación de contenedores")

    for nombre in CONTENEDORES:
        try:
            contenedor = client.containers.get(nombre)
            estado = contenedor.status
            stats = contenedor.stats(stream=False)

            # Calcular uso de CPU
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                       stats['precpu_stats']['cpu_usage']['total_usage']
            system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                          stats['precpu_stats']['system_cpu_usage']
            num_cpus = stats['cpu_stats']['online_cpus']
            cpu_percent = (cpu_delta / system_delta) * num_cpus * 100

            # Calcular uso de RAM
            ram_usado = stats['memory_stats']['usage'] / (1024 * 1024)
            ram_limite = stats['memory_stats']['limit'] / (1024 * 1024)
            ram_percent = (ram_usado / ram_limite) * 100

            log.info(f"✅ {nombre}: {estado} | CPU: {cpu_percent:.2f}% | RAM: {ram_usado:.1f}MB ({ram_percent:.1f}%)")

            # Alerta si CPU supera 80%
            if cpu_percent > 80:
                log.warning(f"⚠️  ALERTA: {nombre} CPU al {cpu_percent:.2f}%")

            # Alerta si RAM supera 80%
            if ram_percent > 80:
                log.warning(f"⚠️  ALERTA: {nombre} RAM al {ram_percent:.1f}%")

        except docker.errors.NotFound:
            log.error(f"❌ {nombre}: CONTENEDOR NO ENCONTRADO")
        except Exception as e:
            log.error(f"❌ {nombre}: ERROR - {e}")

def verificar_nginx():
    """Verifica que Nginx responde correctamente"""
    try:
        respuesta = requests.get(NGINX_URL, timeout=5)
        if respuesta.status_code == 200:
            log.info(f"✅ Nginx HTTP: OK (status {respuesta.status_code})")
        else:
            log.warning(f"⚠️  Nginx HTTP: status inesperado {respuesta.status_code}")
    except requests.exceptions.ConnectionError:
        log.error("❌ Nginx HTTP: SIN RESPUESTA - servicio caído")
    except requests.exceptions.Timeout:
        log.error("❌ Nginx HTTP: TIMEOUT - respuesta muy lenta")

def ejecutar_monitoreo():
    """Función principal que corre todas las verificaciones"""
    verificar_contenedores()
    verificar_nginx()

# ── Programar ejecución cada 30 segundos ──────────────────────
schedule.every(30).seconds.do(ejecutar_monitoreo)

if __name__ == '__main__':
    log.info("🛡️  Bunker SRE Monitor iniciado")
    log.info(f"📋 Monitoreando: {', '.join(CONTENEDORES)}")
    log.info("⏱️  Intervalo: cada 30 segundos")
    log.info("=" * 50)

    # Ejecutar inmediatamente al arrancar
    ejecutar_monitoreo()

    # Luego cada 30 segundos
    while True:
        schedule.run_pending()
        time.sleep(1)
