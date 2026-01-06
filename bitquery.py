import uuid
import base58
from typing import Dict, Callable, Optional
from confluent_kafka import Consumer, KafkaError, KafkaException
from google.protobuf.message import DecodeError
from google.protobuf.descriptor import FieldDescriptor
import config

from evm import dex_pool_block_message_pb2


def convert_bytes(value, encoding='base58'):
    """Convert bytes to string representation."""
    if encoding == 'base58':
        return base58.b58encode(value).decode()
    return '0x' + value.hex()


def protobuf_to_dict(msg, encoding='base58'):
    """Convert protobuf message to dictionary."""
    result = {}
    for field in msg.DESCRIPTOR.fields:
        value = getattr(msg, field.name)

        if field.label == FieldDescriptor.LABEL_REPEATED:
            if not value:
                continue
            result[field.name] = []
            for item in value:
                if field.type == FieldDescriptor.TYPE_MESSAGE:
                    result[field.name].append(protobuf_to_dict(item, encoding))
                elif field.type == FieldDescriptor.TYPE_BYTES:
                    result[field.name].append(convert_bytes(item, encoding))
                else:
                    result[field.name].append(item)

        elif field.containing_oneof:
            if msg.WhichOneof(field.containing_oneof.name) == field.name:
                if field.type == FieldDescriptor.TYPE_MESSAGE:
                    result[field.name] = protobuf_to_dict(value, encoding)
                elif field.type == FieldDescriptor.TYPE_BYTES:
                    result[field.name] = convert_bytes(value, encoding)
                else:
                    result[field.name] = value

        elif field.type == FieldDescriptor.TYPE_MESSAGE:
            if msg.HasField(field.name):
                result[field.name] = protobuf_to_dict(value, encoding)

        elif field.type == FieldDescriptor.TYPE_BYTES:
            result[field.name] = convert_bytes(value, encoding)

        else:
            result[field.name] = value

    return result


def convert_hex_to_int(data):
    """Recursively convert hex strings to integers/floats for known numeric fields."""
    numeric_hex_fields = {
        'Number', 'BaseFee', 'ParentNumber', 'PreBalance', 'PostBalance',
        'MaxAmountIn', 'MaxAmountOut', 'MinAmountOut', 'MinAmountIn',
        'AmountCurrencyA', 'AmountCurrencyB'
    }
    
    # Fields that should be numeric but might come as strings (decimal or hex)
    numeric_fields = {
        'SlippageBasisPoints', 'Price', 'AtoBPrice', 'BtoAPrice'
    }
    
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if key in numeric_hex_fields and isinstance(value, str) and value:
                # Try hex conversion first
                try:
                    result[key] = int(value, 16)
                except ValueError:
                    # Try decimal conversion
                    try:
                        if '.' in value:
                            result[key] = float(value)
                        else:
                            result[key] = int(value)
                    except ValueError:
                        result[key] = value
            elif key in numeric_fields and isinstance(value, str) and value:
                # For numeric fields, try decimal first, then hex
                try:
                    if '.' in value:
                        result[key] = float(value)
                    else:
                        result[key] = int(value)
                except ValueError:
                    # Try hex as fallback
                    try:
                        result[key] = int(value, 16)
                    except ValueError:
                        result[key] = value
            elif isinstance(value, (dict, list)):
                result[key] = convert_hex_to_int(value)
            else:
                result[key] = value
        return result
    elif isinstance(data, list):
        return [convert_hex_to_int(item) for item in data]
    else:
        return data


class BitqueryStream:
    """Bitquery Kafka stream consumer for DEX pool events."""
    
    def __init__(self, topic: str = 'eth.dexpools.proto', group_id_suffix: Optional[str] = None):
        """
        Initialize Bitquery stream consumer.
        
        Args:
            topic: Kafka topic to subscribe to
            group_id_suffix: Optional suffix for consumer group ID
        """
        self.topic = topic
        group_id_suffix = group_id_suffix or uuid.uuid4().hex
        
        conf = {
            'bootstrap.servers': 'rpk0.bitquery.io:9092,rpk1.bitquery.io:9092,rpk2.bitquery.io:9092',
            'group.id': f'{config.eth_username}-group-{group_id_suffix}',
            'session.timeout.ms': 30000,
            'security.protocol': 'SASL_PLAINTEXT',
            'ssl.endpoint.identification.algorithm': 'none',
            'sasl.mechanisms': 'SCRAM-SHA-512',
            'sasl.username': config.eth_username,
            'sasl.password': config.eth_password,
            'auto.offset.reset': 'latest',
        }
        
        self.consumer = Consumer(conf)
        self.consumer.subscribe([topic])
    
    def parse_message(self, buffer: bytes) -> Optional[Dict]:
        """
        Parse a Kafka message buffer into a dictionary.
        
        Args:
            buffer: Raw message bytes from Kafka
            
        Returns:
            Parsed dictionary or None if parsing fails
        """
        try:
            price_feed = dex_pool_block_message_pb2.DexPoolBlockMessage()
            price_feed.ParseFromString(buffer)
            
            data_dict = protobuf_to_dict(price_feed, encoding='hex')
            data_dict = convert_hex_to_int(data_dict)
            
            return data_dict
        except DecodeError as err:
            print(f"Protobuf decoding error: {err}")
            return None
        except Exception as err:
            print(f"Error parsing message: {err}")
            return None
    
    def poll(self, timeout: float = 1.0) -> Optional[Dict]:
        """
        Poll for a new message from Kafka.
        
        Args:
            timeout: Poll timeout in seconds
            
        Returns:
            Parsed message dictionary or None if no message
        """
        msg = self.consumer.poll(timeout=timeout)
        
        if msg is None:
            return None
        
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                return None
            else:
                raise KafkaException(msg.error())
        
        buffer = msg.value()
        return self.parse_message(buffer)
    
    def stream(self, callback: Callable[[Dict], None], stop_event=None):
        """
        Stream messages and call callback for each message.
        
        Args:
            callback: Function to call with each parsed message
            stop_event: Optional event to signal stopping (not implemented, use KeyboardInterrupt)
        """
        try:
            while True:
                data_dict = self.poll()
                if data_dict is not None:
                    callback(data_dict)
        except KeyboardInterrupt:
            print("Stopping stream...")
        finally:
            self.close()
    
    def close(self):
        """Close the Kafka consumer."""
        self.consumer.close()

