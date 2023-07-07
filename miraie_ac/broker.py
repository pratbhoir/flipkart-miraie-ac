from asyncio_mqtt import Client, Message, MqttError
import asyncio
import ssl
import certifi
import random
import json
from .enums import *
from .user import User


class MirAIeBroker:
    host = "mqtt.miraie.in"
    port = 8883
    use_ssl = True
    client_id = f"ha-mirae-mqtt-{random.randint(0, 1000)}"
    reconnect_interval = 5  # In seconds

    def __init__(self) -> None:
        self.status_callbacks: dict[str, callable] = {}

    def register_device_callback(self, topic: str, callback):
        self.status_callbacks[topic] = callback

    def remove_device_callback(self, topic: str):
        self.status_callbacks.pop(topic, None)

    def set_topics(self, topics: list[str]):
        self.commandTopics = topics

    async def on_connect(self, client: Client):
        for topic in self.commandTopics:
            print("Subscribing to topic: ", topic)
            await client.subscribe(topic)

    def on_message(self, client: Client, message: Message):
        parsed = json.loads(message.payload.decode("utf-8"))
        func = self.status_callbacks.get(message.topic.value)
        func(parsed)

    async def connect(self, username: str, access_token: User, get_token):
        # Set on_token_expire callback
        password = access_token

        context = None

        if self.use_ssl:
            context = ssl.create_default_context(cafile=certifi.where())

        client = Client(
            hostname=self.host,
            port=self.port,
            username=username,
            password=password,
            tls_context=context,
        )

        while True:
            try:
                async with client:
                    async with client.messages() as messages:
                        await self.on_connect(client)

                        async for message in messages:
                            self.on_message(client, message)

            except MqttError as error:
                print(
                    f'Error "{error}". Reconnecting in {self.reconnect_interval} seconds.'
                )
                password = await get_token()
                await asyncio.sleep(self.reconnect_interval)

    def build_base_payload(self):
        return {
            "ki": 1,
            "cnt": "an",
            "sid": "1",
        }

    # Power
    def build_power_payload(self, power: PowerMode):
        payload = self.build_base_payload()
        payload["ps"] = str(power.value)
        return payload

    def set_power(self, topic: str, power: PowerMode):
        self.client.publish(topic, json.dumps(self.build_power_payload(power)))

    # Temperature
    def build_temperature_payload(self, temperature: float):
        payload = self.build_base_payload()
        payload["actmp"] = str(temperature)
        return payload

    def set_temperature(self, topic: str, temperature: float):
        self.client.publish(
            topic, json.dumps(self.build_temperature_payload(temperature))
        )

    # HVAC Mode
    def build_hvac_mode_payload(self, mode: HVACMode):
        payload = self.build_base_payload()
        payload["acmd"] = str(mode.value)
        return payload

    def set_hvac_mode(self, topic: str, mode: HVACMode):
        self.client.publish(topic, json.dumps(self.build_hvac_mode_payload(mode)))

    # Fan Mode
    def build_fan_mode_payload(self, mode: FanMode):
        payload = self.build_base_payload()
        payload["acfs"] = str(mode.value)
        return payload

    def set_fan_mode(self, topic: str, mode: FanMode):
        self.client.publish(topic, json.dumps(self.build_fan_mode_payload(mode)))

    # Preset Mode
    def build_preset_mode_payload(self, mode: PresetMode):
        payload = self.build_base_payload()

        if mode == PresetMode.NONE:
            payload["acem"] = "off"
            payload["acpm"] = "off"
        elif mode == PresetMode.ECO:
            payload["acem"] = "on"
            payload["acpm"] = "off"
            payload["actmp"] = 26.0
        elif mode == PresetMode.BOOST:
            payload["acem"] = "off"
            payload["acpm"] = "on"
        return payload

    def set_preset_mode(self, topic: str, mode: PresetMode):
        self.client.publish(topic, json.dumps(self.build_preset_mode_payload(mode)))

    # Swing Mode
    def build_swing_mode_payload(self, mode: SwingMode):
        payload = self.build_base_payload()
        payload["acvs"] = mode.value
        return payload

    def set_swing_mode(self, topic: str, mode: SwingMode):
        self.client.publish(topic, json.dumps(self.build_swing_mode_payload(mode)))
