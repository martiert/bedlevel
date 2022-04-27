import time


def remove_header(io):
    time.sleep(10)
    io.reset_input_buffer()


class Printer:
    def __init__(self, port, dimensions):
        self._port = port
        x_max, y_max, x_offset, y_offset = dimensions
        self._x_max = x_max
        self._y_max = y_max
        self._x_min = x_offset
        self._y_min = y_offset

    def connect(self):
        self._port.write(b'G21\n')
        self._port.write(b'G90\n')
        self._port.reset_input_buffer()

    def auto_home(self):
        self._run_command(b'G1 F6000\n')
        self._run_command(b'G28\n')
        self._run_command(b'G1 X0 Y0\n')
        self._port.reset_input_buffer()

    def set_bed_temperature(self, temp):
        self._run_command(f'M140 S{temp}\n'.encode())
        self._port.reset_input_buffer()

        temperature = 0
        while temperature < temp:
            line = self._run_command(b'M105\n').decode().split()
            for value in line:
                if value.startswith('B:'):
                    temperature = float(value[2:])
                    break
            time.sleep(2)

    def check_bedlevel(self):
        return self.check_bed_with_NxN_points(2, 2)

    def check_bed_with_NxN_points(self, x_points, y_points):
        x_points -= 1
        y_points -= 1
        return self.check_with_point_offset(
            (self._x_max - self._x_min) / x_points,
            (self._y_max - self._y_min) / y_points)

    def check_with_point_offset(self, x_offset, y_offset):
        x = self._x_min
        y = self._y_min

        result = []

        while True:
            result.append(self.get_z_offset(x, y))
            x += x_offset
            if x > self._x_max or x < self._x_min:
                x -= x_offset
                x_offset *= -1
                y += y_offset

            if y > self._y_max:
                return result

    def get_z_offset(self, x, y):
        output = ''
        for i in range(10):
            output = self._run_command(f'G30 X{x} Y{y}\n'.encode()).decode()
            lines = output.split('\n')
            for line in lines:
                if line.startswith('Bed X: '):
                    components = line.split()
                    return (
                            float(components[2]),
                            float(components[4]),
                            float(components[6]))
        raise RuntimeError(reason=output)

    def _run_command(self, command):
        self._port.write(command)
        return self._read()

    def _read(self):
        output = b''
        while True:
            line = self._port.readline()
            if b'echo:busy:' not in line:
                output += line
            if line.startswith(b'ok'):
                return output


    def __enter__(self):
        remove_header(self._port)
        self.connect()
        return self

    def __exit__(self, type, value, traceback):
        self._port.write(b'M140 S0\n')
