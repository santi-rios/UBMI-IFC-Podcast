"""
Audio generation for podcast episodes
"""

import asyncio
from typing import Optional, Dict
from pathlib import Path
import os

# Robust imports for both package and notebook usage
try:
    from ..utils.logger import get_logger
    from ..utils.config import load_config
except ImportError:
    # Fallback for direct execution or notebook usage
    from utils.logger import get_logger
    from utils.config import load_config


class AudioGenerator:
    """Generate audio from podcast scripts using TTS"""
    
    def __init__(self, config: Dict = None):
        self.config = config or load_config()
        self.logger = get_logger(__name__)
        self.provider = self.config['audio']['provider']
        
    async def generate_audio(self, script_text: str, 
                           output_path: str = None,
                           voice_id: str = None) -> str:
        """
        Generate audio from script text
        
        Args:
            script_text: The podcast script text
            output_path: Path to save audio file
            voice_id: Voice ID to use (provider-specific)
            
        Returns:
            Path to generated audio file
        """
        if not output_path:
            from ..utils.config import get_output_dir
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = get_output_dir() / "podcasts" / f"podcast_{timestamp}.mp3"
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Clean script text for TTS
        clean_text = self._clean_script_for_tts(script_text)
        
        if self.provider == 'elevenlabs':
            return await self._generate_elevenlabs_audio(clean_text, output_path, voice_id)
        elif self.provider == 'azure':
            return await self._generate_azure_audio(clean_text, output_path, voice_id)
        else:
            raise ValueError(f"Unsupported audio provider: {self.provider}")
    
    def _clean_script_for_tts(self, script_text: str) -> str:
        """Clean script text for better TTS output"""
        # Remove markdown formatting
        import re
        
        # Remove headers
        text = re.sub(r'^#{1,6}\s+', '', script_text, flags=re.MULTILINE)
        
        # Remove markdown links
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        
        # Remove markdown bold/italic
        text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)
        text = re.sub(r'\*([^\*]+)\*', r'\1', text)
        
        # Remove multiple newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove timing cues (like [00:30])
        text = re.sub(r'\[\d{2}:\d{2}\]', '', text)
        
        # Add pauses for better speech flow
        text = re.sub(r'\.(\s+)', r'.\n', text)  # Pause after sentences
        text = re.sub(r'\n{2,}', '\n\n', text)  # Standardize paragraph breaks
        
        return text.strip()
    
    async def _generate_elevenlabs_audio(self, text: str, 
                                       output_path: Path,
                                       voice_id: str = None) -> str:
        """Generate audio using ElevenLabs API"""
        try:
            from elevenlabs import generate, save, set_api_key
            
            # Set API key
            api_key = self.config['api_keys']['elevenlabs']
            if not api_key:
                raise ValueError("ElevenLabs API key not found")
            
            set_api_key(api_key)
            
            # Use default voice if none specified
            voice_id = voice_id or self.config['audio']['voice_id']
            
            self.logger.info(f"Generating audio with ElevenLabs, voice: {voice_id}")
            
            # Generate audio
            audio = generate(
                text=text,
                voice=voice_id,
                model="eleven_monolingual_v1"
            )
            
            # Save audio file
            save(audio, str(output_path))
            
            self.logger.info(f"Audio saved to {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"ElevenLabs audio generation failed: {str(e)}")
            raise
    
    async def _generate_azure_audio(self, text: str, 
                                  output_path: Path,
                                  voice_id: str = None) -> str:
        """Generate audio using Azure Cognitive Services"""
        try:
            import azure.cognitiveservices.speech as speechsdk
            
            # Get Azure credentials from config
            subscription_key = self.config.get('azure', {}).get('speech_key')
            region = self.config.get('azure', {}).get('region', 'eastus')
            
            if not subscription_key:
                raise ValueError("Azure Speech API key not found")
            
            # Create speech config
            speech_config = speechsdk.SpeechConfig(
                subscription=subscription_key, 
                region=region
            )
            
            # Set voice
            voice_name = voice_id or "en-US-AriaNeural"
            speech_config.speech_synthesis_voice_name = voice_name
            
            # Set output format
            speech_config.set_speech_synthesis_output_format(
                speechsdk.SpeechSynthesisOutputFormat.Audio48Khz192KBitRateMonoMp3
            )
            
            self.logger.info(f"Generating audio with Azure Speech, voice: {voice_name}")
            
            # Create synthesizer
            audio_config = speechsdk.audio.AudioOutputConfig(filename=str(output_path))
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=speech_config, 
                audio_config=audio_config
            )
            
            # Generate audio
            result = synthesizer.speak_text_async(text).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                self.logger.info(f"Audio saved to {output_path}")
                return str(output_path)
            else:
                raise Exception(f"Speech synthesis failed: {result.reason}")
                
        except Exception as e:
            self.logger.error(f"Azure audio generation failed: {str(e)}")
            raise
    
    async def enhance_audio(self, audio_path: str, 
                          output_path: str = None) -> str:
        """
        Enhance audio quality (noise reduction, normalization, etc.)
        
        Args:
            audio_path: Path to input audio file
            output_path: Path for enhanced audio file
            
        Returns:
            Path to enhanced audio file
        """
        if not output_path:
            input_path = Path(audio_path)
            output_path = input_path.parent / f"{input_path.stem}_enhanced{input_path.suffix}"
        
        try:
            from pydub import AudioSegment
            from pydub.effects import normalize, compress_dynamic_range
            
            self.logger.info(f"Enhancing audio: {audio_path}")
            
            # Load audio
            audio = AudioSegment.from_file(audio_path)
            
            # Normalize volume
            audio = normalize(audio)
            
            # Apply light compression
            audio = compress_dynamic_range(audio, threshold=-20.0, ratio=4.0)
            
            # Add fade in/out
            audio = audio.fade_in(1000).fade_out(1000)  # 1 second fades
            
            # Export enhanced audio
            audio.export(output_path, format="mp3", bitrate="192k")
            
            self.logger.info(f"Enhanced audio saved to {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"Audio enhancement failed: {str(e)}")
            # Return original path if enhancement fails
            return audio_path
    
    def get_audio_info(self, audio_path: str) -> Dict:
        """Get information about an audio file"""
        try:
            from pydub import AudioSegment
            
            audio = AudioSegment.from_file(audio_path)
            
            return {
                'duration_seconds': len(audio) / 1000.0,
                'duration_formatted': self._format_duration(len(audio) / 1000.0),
                'channels': audio.channels,
                'frame_rate': audio.frame_rate,
                'sample_width': audio.sample_width,
                'file_size_mb': os.path.getsize(audio_path) / (1024 * 1024)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get audio info: {str(e)}")
            return {}
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in MM:SS format"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    async def create_intro_outro(self, intro_text: str = None, 
                               outro_text: str = None) -> Dict[str, str]:
        """
        Create standard intro and outro audio clips
        
        Args:
            intro_text: Custom intro text (uses default if None)
            outro_text: Custom outro text (uses default if None)
            
        Returns:
            Dictionary with paths to intro and outro audio files
        """
        default_intro = """
        Bienvenidos al podcast científico del Instituto de Fisiología Celular de la UNAM. 
        En este episodio exploraremos los avances más recientes en investigación biomédica 
        que están relacionados con nuestras líneas de investigación.
        """
        
        default_outro = """
        Gracias por acompañarnos en este episodio. Para más información sobre nuestras 
        investigaciones, visiten el sitio web del Instituto de Fisiología Celular de la UNAM. 
        Nos vemos en el próximo episodio.
        """
        
        intro_text = intro_text or default_intro.strip()
        outro_text = outro_text or default_outro.strip()
        
        # Generate intro
        intro_path = await self.generate_audio(
            intro_text,
            output_path=None  # Will auto-generate path
        )
        
        # Generate outro
        outro_path = await self.generate_audio(
            outro_text,
            output_path=None  # Will auto-generate path
        )
        
        return {
            'intro': intro_path,
            'outro': outro_path
        }


async def main():
    """Test function"""
    generator = AudioGenerator()
    
    sample_script = """
    Welcome to today's science podcast. We'll be discussing recent advances in neuroscience research.
    
    Recent studies have shown fascinating insights into how the brain processes memory formation.
    """
    
    try:
        # This would require API keys to work
        print("Audio generator initialized")
        print("Script cleaned for TTS:")
        print(generator._clean_script_for_tts(sample_script))
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
