import sys
import logging
import serial
from aiohttp import web

from .Printer import Printer


def create_serial(device, baudrate):
    with serial.Serial(device, baudrate) as p:
        yield p
        yield None


class LogFormatter(logging.Formatter):
    grey = '\x1b[38;20m'
    yellow = '\x1b[33;20m'
    red = '\x1b[31;20m'
    dark_red = '\x1b[31;1m'

    levels = {
        logging.DEBUG: grey,
        logging.INFO: grey,
        logging.WARNING: yellow,
        logging.ERROR: red,
        logging.CRITICAL: dark_red
    }
    reset = '\x1b[0m'
    format_str='[%(asctime)s] %(levelname)s: %(message)s'

    def format(self, record):
        log_format = self.levels[record.levelno] + self.format_str + self.reset
        formatter = logging.Formatter(log_format)
        return formatter.format(record)


logger = logging.getLogger('bedlevel')
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
handler.setFormatter(LogFormatter())

logger.addHandler(handler)

serial_gen = create_serial('/dev/ttyUSB0', 115200)
port = next(serial_gen)


def sort(e):
    return e[1] * 1000 + e[0]


def make_points_result(points):
    points.sort(key=sort)
    x_points, y_points, z_points = list(zip(*points))
    x = list(sorted(list(set(x_points))))
    chunk_size = len(x)
    z = []
    for i in range(0, len(z_points), chunk_size):
        z.append(z_points[i:i+chunk_size])

    return {
        'x': x,
        'y': list(sorted(list(set(y_points)))),
        'z': z
    }


with Printer(port, [275, 280, 15, 10]) as printer:
    logger.info('Auto home')
    printer.auto_home()

    routes = web.RouteTableDef()

    @routes.post('/temp/{temperature}')
    async def set_temp(request):
        temperature = int(request.match_info['temperature'])
        logging.info(f'Setting temperature to {temperature}')
        printer.set_bed_temperature(temperature)
        return web.Response()

    @routes.post('/autohome')
    async def set_temp(request):
        logging.info('Auto homing the device')
        printer.auto_home()
        return web.Response()

    @routes.get('/corners')
    async def set_temp(request):
        logging.info('Fetching corner levels')
        corners = printer.check_bedlevel()
        result = make_points_result(corners)
        return web.json_response(result)

    @routes.get('/points/{x_points}/{y_points}')
    async def set_temp(request):
        x_points = int(request.match_info['x_points'])
        y_points = int(request.match_info['y_points'])
        logging.info(f'Getting points for a {x_points}x{x_points} grid')
        points = printer.check_bed_with_NxN_points(
                x_points,
                y_points)
        result = make_points_result(points)
        return web.json_response(result)

    app = web.Application()
    app.add_routes(routes)
    web.run_app(app, host='localhost')
