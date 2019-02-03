import json
import logging
from asyncio import open_connection, create_task, Lock

from aiortc.mediastreams import MediaStreamError
from av.audio.resampler import AudioResampler

log = logging.getLogger('')


class KaldiSink:
    """
    This class is a proxy between the client browser (aka peer connection) and the Kaldi server.

    It creates 2 tasks that transfer data between the two:
    1. __run_audio_xfer transfers audio from the browser (mic) to the Kaldi server
    2. __run_text_xfer transfers text from the Kaldi server to the browser
    """

    def __init__(self, user_connection, kaldi_server):
        self.__resampler = AudioResampler(format='s16', layout='mono', rate=kaldi_server.samplerate)

        self.__pc = user_connection
        self.__audio_task = None
        self.__text_task = None

        self.__ks = kaldi_server
        self.__kaldi_reader = None
        self.__kaldi_writer = None

    async def set_audio_track(self, track):
        self.__track = track
        try:
            self.__kaldi_reader, self.__kaldi_writer = await open_connection(host=self.__ks.host, port=self.__ks.port)
        except:
            log.exception("Error opening conenction to Kaldi server")
            self.__pc.close()
            await self.__ks.free()
            return
        self.__text_task = create_task(self.__run_text_xfer())
        self.__audio_task = create_task(self.__run_audio_xfer())

    async def set_text_channel(self, channel):
        self.__channel = channel

    async def stop(self):
        if self.__audio_task is not None:
            self.__audio_task.cancel()
            self.__audio_task = None
        if self.__text_task is not None:
            self.__text_task.cancel()
            self.__text_task = None
        if self.__kaldi_writer:
            self.__kaldi_writer.close()
            self.__kaldi_writer = None
            await self.__ks.free()

    async def __run_audio_xfer(self):
        while True:
            try:
                frame = await self.__track.recv()
            except MediaStreamError:
                self.__kaldi_writer.close()
                await self.__ks.free()
                return
            frame = self.__resampler.resample(frame)
            data = frame.to_ndarray()
            self.__kaldi_writer.write(data.tobytes())

    async def __run_text_xfer(self):
        while True:
            if self.__kaldi_reader.at_eof():
                self.__pc.close()
                await self.__ks.free()
                return
            a = await self.__kaldi_reader.read(256)
            if self.__channel:
                self.__channel.send(str(a, encoding='utf-8'))


class KaldiServer:
    """
    This class describes the Kaldi server resource. It is a representation of a running instance of the Kaldi server
    together with its parameters.
    """

    def __init__(self, srv_config):
        for key in ['name', 'host', 'port', 'samplerate']:
            if key in srv_config:
                setattr(self, key, srv_config[key])

    async def free(self):
        """
        Relases the resource back to the queue.
        :return:
        """

        await kaldi_server_queue.put(self)


class KaldiServerQueue:
    """
    This class represents the servers available for usage by the clients.

    When a server is used it is removed from the queue. After it is released it gets back in the queue.
    """

    def __init__(self):
        self.__servers = set()
        self.__lock = Lock()

    def load(self, config):
        with open(config) as f:
            servers = json.load(f)

        for server in servers:
            self.__servers.add(KaldiServer(server))

    async def get(self):
        async with self.__lock:
            if self.__servers:
                try:
                    return self.__servers.pop()
                except KeyError:
                    return None

    async def put(self, server):
        async with self.__lock:
            self.__servers.add(server)


kaldi_server_queue = KaldiServerQueue()
