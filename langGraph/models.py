from django.db import models
import json
from datetime import datetime
from datetime import datetime
import pytz
from django.utils.timezone import make_aware, get_current_timezone

class Checkpoint(models.Model):
    checkpoint_id = models.CharField(max_length=255, primary_key=True)  # No puede ser NULL, clave primaria
    parent_checkpoint_id = models.CharField(max_length=255, null=True, blank=True)  # Puede ser NULL
    thread_id = models.CharField(max_length=255, null=True, blank=True)  # Puede ser NULL
    metadata = models.JSONField()  # No puede ser NULL
    checkpoint = models.JSONField()

    class Meta:
        db_table = "checkpoints"
        managed = False

 # cursor.execute("DELETE FROM checkpoints WHERE checkpoint_id = %s", [self.checkpoint_id])

    def get_timestamp(self):
        """Extrae el timestamp del checkpoint y lo formatea en estilo latino"""
        try:
            ts_str = self.checkpoint.get('ts', '')
            if ts_str:
                # Convertir el string ISO a objeto datetime (asegurar que sea UTC)
                ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                
                # Asegurar que el datetime tenga información de zona horaria
                if ts.tzinfo is None:
                    ts = make_aware(ts, pytz.UTC)  # Asegurar que está en UTC

                # Convertir a la zona horaria configurada en Django (UTC-4 si es La Paz)
                ts = ts.astimezone(get_current_timezone())

                # Formatear en estilo latino (dd/mm/yyyy hh:mm:ss)
                return ts.strftime('%d/%m/%Y %H:%M:%S')
            return ''
        except Exception as e:
            return ''
    get_timestamp.short_description = 'Fecha y Hora'

    def formatted_metadata(self):
        """Retorna el metadata formateado de manera legible"""
        return json.dumps(self.metadata, indent=2, ensure_ascii=False)
    formatted_metadata.short_description = 'Metadata Formateado'

    def get_summary(self):
        """Extrae el resumen de la conversación del metadata"""
        try:
            return self.metadata.get('writes', {}).get('summary_conversation', {}).get('summary', '')
        except:
            return ''
    get_summary.short_description = 'Resumen de Conversación'

    def get_step(self):
        """Extrae el paso actual del metadata"""
        return self.metadata.get('step', '')
    get_step.short_description = 'Paso'

    def get_source(self):
        """Extrae la fuente del metadata"""
        return self.metadata.get('source', '')
    get_source.short_description = 'Fuente'

    def get_message_content(self):
        """Extrae el contenido del mensaje según su tipo"""
        try:
            # Buscar en summary_conversation
            if 'summary_conversation' in self.metadata.get('writes', {}):
                return self.get_summary()
            
            # Buscar en process_input (mensajes AI)
            process_input = self.metadata.get('writes', {}).get('process_input', {})
            if 'messages' in process_input:
                messages = process_input['messages']
                if isinstance(messages, dict) and messages.get('kwargs', {}).get('type') == 'ai':
                    return messages.get('kwargs', {}).get('content', '')
            
            # Mantener la búsqueda en initial (mensajes AI - formato anterior)
            initial = self.metadata.get('writes', {}).get('initial', {})
            if 'messages' in initial:
                messages = initial['messages']
                if isinstance(messages, dict):
                    messages = [messages]
                for msg in messages:
                    if isinstance(msg, dict) and msg.get('kwargs', {}).get('type') == 'ai':
                        return msg.get('kwargs', {}).get('content', '')
            
            # Buscar en __start__ (mensajes Human)
            start = self.metadata.get('writes', {}).get('__start__', {})
            if 'messages' in start:
                messages = start['messages']
                if isinstance(messages, dict):
                    messages = [messages]
                for msg in messages:
                    if isinstance(msg, dict) and msg.get('kwargs', {}).get('type') == 'human':
                        return msg.get('kwargs', {}).get('content', '')
            
            return ''
        except:
            return ''
    get_message_content.short_description = 'Mensaje'

    def get_message_type(self):
        """Determina el tipo de mensaje"""
        try:
            if 'summary_conversation' in self.metadata.get('writes', {}):
                return 'Summary'
            
            # Buscar en process_input (mensajes AI)
            process_input = self.metadata.get('writes', {}).get('process_input', {})
            if 'messages' in process_input:
                messages = process_input['messages']
                if isinstance(messages, dict) and messages.get('kwargs', {}).get('type') == 'ai':
                    return 'AI'
            
            # Buscar en initial (mensajes AI - formato anterior)
            initial = self.metadata.get('writes', {}).get('initial', {})
            if 'messages' in initial:
                messages = initial['messages']
                if isinstance(messages, dict):
                    messages = [messages]
                for msg in messages:
                    if isinstance(msg, dict) and msg.get('kwargs', {}).get('type') == 'ai':
                        return 'AI'
            
            # Buscar en __start__ (mensajes Human)
            start = self.metadata.get('writes', {}).get('__start__', {})
            if 'messages' in start:
                messages = start['messages']
                if isinstance(messages, dict):
                    messages = [messages]
                for msg in messages:
                    if isinstance(msg, dict) and msg.get('kwargs', {}).get('type') == 'human':
                        return 'User'
            
            return ''
        except:
            return ''
    get_message_type.short_description = 'Tipo de Mensaje'

    def __str__(self):
        return f"Checkpoint {self.checkpoint_id}"
