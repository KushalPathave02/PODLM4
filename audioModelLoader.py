from transformers import AutoModel, AutoProcessor, BarkModel
import numpy as np
from pydub import AudioSegment
import torch
import scipy.io.wavfile

def loadModel():
    processor = AutoProcessor.from_pretrained("suno/bark-small")
    model = BarkModel.from_pretrained("suno/bark-small", torch_dtype=torch.float16, attn_implementation="flash_attention_2").to("cuda:0")
    model = model.to_bettertransformer().to("cuda:0")
    return model.to("cuda:0"), processor

def generateAudio(model, processor, text, voice_preset):
    inputs = processor(text, voice_preset=voice_preset).to("cuda:0")
    inputs['attention_mask'] = inputs['input_ids'].ne(processor.tokenizer.pad_token_id).long().to("cuda:0")
    audio_array = model.generate(**inputs)
    audio_array = audio_array.cpu().numpy().squeeze()
    audio_array = np.int16(audio_array * 32767)
    return audio_array, model.generation_config.sample_rate