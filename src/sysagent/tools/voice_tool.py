"""
Voice tool for SysAgent CLI.
"""

import subprocess
import os
import tempfile
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from .base import BaseTool, ToolMetadata, ToolResult, register_tool
from ..types import ToolCategory
from ..utils.platform import detect_platform, Platform


@register_tool
class VoiceTool(BaseTool):
    """Tool for voice input/output capabilities."""
    
    def _get_metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        return ToolMetadata(
            name="voice_tool",
            description="Voice input, speech recognition, and text-to-speech",
            category=ToolCategory.VOICE,
            permissions=["microphone", "audio"],
            version="1.0.0"
        )

    def _execute(self, action: str, **kwargs) -> ToolResult:
        """Execute voice action."""
        try:
            if action == "speak":
                return self._speak(**kwargs)
            elif action == "listen":
                return self._listen(**kwargs)
            elif action == "record":
                return self._record(**kwargs)
            elif action == "transcribe":
                return self._transcribe(**kwargs)
            elif action == "voices":
                return self._list_voices(**kwargs)
            elif action == "devices":
                return self._list_audio_devices(**kwargs)
            else:
                return ToolResult(
                    success=False,
                    data={},
                    message=f"Unknown action: {action}",
                    error=f"Unsupported action: {action}"
                )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Voice operation failed: {str(e)}",
                error=str(e)
            )

    def _speak(self, **kwargs) -> ToolResult:
        """Convert text to speech."""
        text = kwargs.get("text") or kwargs.get("message")
        voice = kwargs.get("voice")
        rate = kwargs.get("rate", 175)  # Words per minute
        volume = kwargs.get("volume", 1.0)
        output_file = kwargs.get("output")
        
        if not text:
            return ToolResult(
                success=False,
                data={},
                message="No text provided",
                error="Missing text"
            )
        
        try:
            current_platform = detect_platform()
            
            if current_platform == Platform.MACOS:
                cmd = ["say"]
                if voice:
                    cmd.extend(["-v", voice])
                if rate:
                    cmd.extend(["-r", str(rate)])
                if output_file:
                    cmd.extend(["-o", output_file])
                cmd.append(text)
                
                subprocess.run(cmd, capture_output=True, check=True)
                
            elif current_platform == Platform.LINUX:
                # Try espeak, festival, or pico2wave
                success = False
                
                try:
                    cmd = ["espeak"]
                    if rate:
                        cmd.extend(["-s", str(rate)])
                    if output_file:
                        cmd.extend(["-w", output_file])
                    cmd.append(text)
                    subprocess.run(cmd, capture_output=True, check=True)
                    success = True
                except FileNotFoundError:
                    pass
                
                if not success:
                    try:
                        # Use festival
                        subprocess.run(
                            ["festival", "--tts"],
                            input=text.encode(),
                            capture_output=True,
                            check=True
                        )
                        success = True
                    except FileNotFoundError:
                        pass
                
                if not success:
                    try:
                        # Use pico2wave
                        if output_file:
                            wav_file = output_file
                        else:
                            wav_file = tempfile.mktemp(suffix=".wav")
                        
                        subprocess.run(
                            ["pico2wave", "-w", wav_file, text],
                            capture_output=True,
                            check=True
                        )
                        
                        if not output_file:
                            # Play the audio
                            subprocess.run(["aplay", wav_file], capture_output=True)
                            os.remove(wav_file)
                        success = True
                    except FileNotFoundError:
                        pass
                
                if not success:
                    return ToolResult(
                        success=False,
                        data={},
                        message="No TTS engine found (install espeak, festival, or pico2wave)",
                        error="Missing TTS"
                    )
                    
            elif current_platform == Platform.WINDOWS:
                # Use PowerShell with SAPI
                ps_script = f'''
                Add-Type -AssemblyName System.Speech
                $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
                $synth.Rate = {int((rate - 175) / 25)}
                $synth.Volume = {int(volume * 100)}
                '''
                if output_file:
                    ps_script += f'$synth.SetOutputToWaveFile("{output_file}")\n'
                ps_script += f'$synth.Speak("{text}")\n'
                
                subprocess.run(
                    ["powershell", "-Command", ps_script],
                    capture_output=True,
                    check=True
                )
            else:
                return ToolResult(
                    success=False,
                    data={},
                    message="TTS not supported on this platform",
                    error="Unsupported platform"
                )
            
            result_data = {"text": text[:100] + "..." if len(text) > 100 else text}
            if output_file:
                result_data["output_file"] = output_file
                
            return ToolResult(
                success=True,
                data=result_data,
                message=f"Spoke {len(text)} characters"
            )
            
        except subprocess.CalledProcessError as e:
            return ToolResult(
                success=False,
                data={},
                message=f"TTS failed: {e.stderr}",
                error=str(e)
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"TTS failed: {str(e)}",
                error=str(e)
            )

    def _listen(self, **kwargs) -> ToolResult:
        """Listen for voice input and transcribe."""
        duration = kwargs.get("duration", 5)  # seconds
        
        try:
            # Try to use speech_recognition library
            try:
                import speech_recognition as sr
                
                recognizer = sr.Recognizer()
                
                with sr.Microphone() as source:
                    recognizer.adjust_for_ambient_noise(source, duration=1)
                    audio = recognizer.listen(source, timeout=duration)
                
                # Try Google Speech Recognition
                try:
                    text = recognizer.recognize_google(audio)
                    return ToolResult(
                        success=True,
                        data={"text": text, "engine": "google"},
                        message=f"Transcribed: {text}"
                    )
                except sr.UnknownValueError:
                    return ToolResult(
                        success=False,
                        data={},
                        message="Could not understand audio",
                        error="Unrecognized speech"
                    )
                except sr.RequestError as e:
                    return ToolResult(
                        success=False,
                        data={},
                        message=f"Speech service error: {str(e)}",
                        error=str(e)
                    )
                    
            except ImportError:
                return ToolResult(
                    success=False,
                    data={},
                    message="Install SpeechRecognition library: pip install SpeechRecognition",
                    error="Missing dependency"
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Voice input failed: {str(e)}",
                error=str(e)
            )

    def _record(self, **kwargs) -> ToolResult:
        """Record audio to a file."""
        duration = kwargs.get("duration", 10)  # seconds
        output_file = kwargs.get("output") or kwargs.get("path")
        
        if not output_file:
            output_file = tempfile.mktemp(suffix=".wav")
        
        try:
            current_platform = detect_platform()
            
            if current_platform == Platform.MACOS:
                # Use sox (rec)
                subprocess.run(
                    ["rec", "-q", output_file, "trim", "0", str(duration)],
                    capture_output=True,
                    check=True
                )
                
            elif current_platform == Platform.LINUX:
                # Try arecord, sox, or ffmpeg
                success = False
                
                try:
                    subprocess.run(
                        ["arecord", "-d", str(duration), "-f", "cd", output_file],
                        capture_output=True,
                        check=True
                    )
                    success = True
                except FileNotFoundError:
                    pass
                
                if not success:
                    try:
                        subprocess.run(
                            ["rec", "-q", output_file, "trim", "0", str(duration)],
                            capture_output=True,
                            check=True
                        )
                        success = True
                    except FileNotFoundError:
                        pass
                
                if not success:
                    try:
                        subprocess.run(
                            ["ffmpeg", "-f", "alsa", "-i", "default", "-t", str(duration), 
                             "-y", output_file],
                            capture_output=True,
                            check=True
                        )
                        success = True
                    except FileNotFoundError:
                        pass
                
                if not success:
                    return ToolResult(
                        success=False,
                        data={},
                        message="No audio recorder found (install arecord, sox, or ffmpeg)",
                        error="Missing recorder"
                    )
                    
            elif current_platform == Platform.WINDOWS:
                # Use PowerShell with NAudio or ffmpeg
                return ToolResult(
                    success=False,
                    data={},
                    message="Recording on Windows requires ffmpeg",
                    error="Not implemented"
                )
            
            if os.path.exists(output_file):
                return ToolResult(
                    success=True,
                    data={
                        "path": output_file,
                        "duration": duration,
                        "size_bytes": os.path.getsize(output_file)
                    },
                    message=f"Recorded {duration}s of audio to {output_file}"
                )
            else:
                return ToolResult(
                    success=False,
                    data={},
                    message="Recording failed - file not created",
                    error="Recording failed"
                )
                
        except subprocess.CalledProcessError as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Recording failed: {e.stderr}",
                error=str(e)
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Recording failed: {str(e)}",
                error=str(e)
            )

    def _transcribe(self, **kwargs) -> ToolResult:
        """Transcribe an audio file to text."""
        audio_file = kwargs.get("path") or kwargs.get("file")
        
        if not audio_file:
            return ToolResult(
                success=False,
                data={},
                message="No audio file provided",
                error="Missing path"
            )
        
        if not os.path.exists(audio_file):
            return ToolResult(
                success=False,
                data={},
                message=f"Audio file not found: {audio_file}",
                error="File not found"
            )
        
        try:
            # Try speech_recognition library
            try:
                import speech_recognition as sr
                
                recognizer = sr.Recognizer()
                
                with sr.AudioFile(audio_file) as source:
                    audio = recognizer.record(source)
                
                text = recognizer.recognize_google(audio)
                return ToolResult(
                    success=True,
                    data={"text": text, "source": audio_file, "engine": "google"},
                    message=f"Transcribed: {text}"
                )
                
            except ImportError:
                # Try whisper if available
                try:
                    import whisper
                    
                    model = whisper.load_model("base")
                    result = model.transcribe(audio_file)
                    
                    return ToolResult(
                        success=True,
                        data={
                            "text": result["text"],
                            "source": audio_file,
                            "engine": "whisper"
                        },
                        message=f"Transcribed: {result['text']}"
                    )
                    
                except ImportError:
                    return ToolResult(
                        success=False,
                        data={},
                        message="Install SpeechRecognition or openai-whisper for transcription",
                        error="Missing dependency"
                    )
                    
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Transcription failed: {str(e)}",
                error=str(e)
            )

    def _list_voices(self, **kwargs) -> ToolResult:
        """List available TTS voices."""
        try:
            current_platform = detect_platform()
            voices = []
            
            if current_platform == Platform.MACOS:
                result = subprocess.run(
                    ["say", "-v", "?"],
                    capture_output=True,
                    text=True
                )
                for line in result.stdout.strip().split('\n'):
                    parts = line.split()
                    if parts:
                        voices.append({
                            "name": parts[0],
                            "language": parts[1] if len(parts) > 1 else "unknown"
                        })
                        
            elif current_platform == Platform.LINUX:
                # espeak voices
                try:
                    result = subprocess.run(
                        ["espeak", "--voices"],
                        capture_output=True,
                        text=True
                    )
                    for line in result.stdout.strip().split('\n')[1:]:  # Skip header
                        parts = line.split()
                        if len(parts) >= 4:
                            voices.append({
                                "name": parts[3],
                                "language": parts[1]
                            })
                except FileNotFoundError:
                    pass
                    
            elif current_platform == Platform.WINDOWS:
                ps_script = '''
                Add-Type -AssemblyName System.Speech
                $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
                $synth.GetInstalledVoices() | ForEach-Object { $_.VoiceInfo.Name }
                '''
                result = subprocess.run(
                    ["powershell", "-Command", ps_script],
                    capture_output=True,
                    text=True
                )
                for line in result.stdout.strip().split('\n'):
                    if line:
                        voices.append({"name": line, "language": "unknown"})
            
            return ToolResult(
                success=True,
                data={"voices": voices, "count": len(voices)},
                message=f"Found {len(voices)} available voices"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to list voices: {str(e)}",
                error=str(e)
            )

    def _list_audio_devices(self, **kwargs) -> ToolResult:
        """List available audio input devices."""
        try:
            devices = []
            
            # Try pyaudio
            try:
                import pyaudio
                
                p = pyaudio.PyAudio()
                for i in range(p.get_device_count()):
                    info = p.get_device_info_by_index(i)
                    devices.append({
                        "index": i,
                        "name": info["name"],
                        "input_channels": info["maxInputChannels"],
                        "output_channels": info["maxOutputChannels"],
                        "sample_rate": info["defaultSampleRate"]
                    })
                p.terminate()
                
            except ImportError:
                # Fallback to system commands
                current_platform = detect_platform()
                
                if current_platform == Platform.LINUX:
                    result = subprocess.run(
                        ["arecord", "-l"],
                        capture_output=True,
                        text=True
                    )
                    devices.append({"info": result.stdout})
                    
                elif current_platform == Platform.MACOS:
                    result = subprocess.run(
                        ["system_profiler", "SPAudioDataType"],
                        capture_output=True,
                        text=True
                    )
                    devices.append({"info": result.stdout[:500]})
            
            return ToolResult(
                success=True,
                data={"devices": devices, "count": len(devices)},
                message=f"Found {len(devices)} audio devices"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                message=f"Failed to list audio devices: {str(e)}",
                error=str(e)
            )

    def get_usage_examples(self) -> List[str]:
        """Get usage examples for this tool."""
        return [
            "Speak text: voice_tool --action speak --text 'Hello World'",
            "Listen for input: voice_tool --action listen --duration 5",
            "Record audio: voice_tool --action record --duration 10 --output recording.wav",
            "Transcribe audio: voice_tool --action transcribe --path audio.wav",
            "List voices: voice_tool --action voices",
            "List audio devices: voice_tool --action devices",
        ]
