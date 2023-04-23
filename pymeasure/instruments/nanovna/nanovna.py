#
# This file is part of the PyMeasure package.
#
# Copyright (c) 2013-2023 PyMeasure Developers
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

from numpy import array
from pymeasure.adapters import SerialAdapter
from pymeasure.instruments import Instrument
from pymeasure.instruments.validators import strict_discrete_set


class SerialAdapterWithEcho(SerialAdapter):

    echo_termination = '\r\n'
    # write_termination = '\r'
    # read_termination = '\r\nch> '

    def _read_echo(self, **kwargs):
        """Read function but includes scrubbing the echo from the reply.

        :param \\**kwargs: Keyword arguments for the connection itself.
        :returns str: ASCII response of the instrument with echo removed.
        """
        read = self._read_bytes(-1, break_on_termchar=True, **kwargs).decode()
        read = read.replace('ch> ', "").split(self.echo_termination)
        # echo = read[0]
        reply = read[1:-1]

        return ",".join(reply)  # TODO maybe don't return as a single string???


class NanoVNA(Instrument):
    """ Represents the NanoVNA interface for interacting with the instrument.

    .. code-block:: python

    """

    def __init__(self, adapter, name="NanoVNA", **kwargs):
        super().__init__(
            adapter,
            name,
            includeSCPI=False,
            read_termination='\r\nch> ',
            write_termination='\r',
            **kwargs
        )

    def read(self):
        """
        Reads from the instrument including the correct termination characters
        """
        ret = self.adapter._read_echo()
        return ret

    def write(self, command):
        """
        Writes to the instrument including the device address

        :param command: command string to be sent to the instrument
        """
        super().write(command)

    def ask(self, command, query_delay=0):
        """Write a command to the instrument and return the read response.

        :param command: Command string to be sent to the instrument.
        :param query_delay: Delay between writing and reading in seconds.
        :returns: String returned by the device without read_termination.
        """
        self.write(command)
        self.wait_for(query_delay)
        return self.adapter._read_echo()

    help = Instrument.measurement(
        'help',
        """Returns list of available commands. """)

    info = Instrument.measurement(
        'info',
        """Returns device information. """)

    pause = Instrument.measurement(
        'pause',
        """Pauses acquisition. Returns nothing. """)

    resume = Instrument.measurement(
        'resume',
        """Resume acquisition.  Returns nothing. """)

    frequencies = Instrument.measurement("frequencies",
                                         docs=""" Returns frequencies as a list
                                         of floats. """,
                                         # get_process=_process_frequencies,
                                         )

    data = Instrument.measurement("data",
                                  docs=""" Returns a list of strings containing
                                  the complex numbers. """,
                                  )

    trace = Instrument.measurement("trace",
                                   docs=""" Gets the trace settings. """,
                                   # TODO - make this into a control,
                                   )

    power = Instrument.setting('power %d',
                               """ Sets the output power. """,
                               validator=strict_discrete_set,
                               values=[-1, 0, 1, 2, 3],
                               )

    sweep = Instrument.control('sweep',
                               'sweep %i %i %i',
                               """Set the sweep details.  Input is a tuple
                               containing 3 integers.
                               First int is the start frequency (in Hz).
                               Second int is the strop frequency (in Hz).
                               Third int is the number of points in the sweep.
                               Example:  :code:`13000000 16000000 101`.  """,
                               )

    def _process_frequencies(self, freqs):
        return array(freqs.split(","), dtype=float)

    def get_frequencies(self):
        return self._process_frequencies(self.ask("frequencies"))

    def _process_data(self, data):
        data = array(data.replace(" ", ",").split(","), dtype=float)
        return data[::2] + data[1::2] * 1j

    def get_S11_data(self):
        return self._process_data(self.ask("data 0"))

    def get_S21_data(self):
        return self._process_data(self.ask("data 1"))

    def get_cals(self):
        cal_load = self._process_data(self.ask("data 2"))
        cal_open = self._process_data(self.ask("data 3"))
        cal_short = self._process_data(self.ask("data 4"))
        cal_thru = self._process_data(self.ask("data 5"))
        cal_isoln = self._process_data(self.ask("data 6"))
        return {"load": cal_load, "open": cal_open, "short": cal_short,
                "thru": cal_thru, "isoln": cal_isoln}
