"""Unit tests for Hybrid Voice Security Microservice (Wav2Vec + KAN + GAT)."""
from __future__ import annotations

import numpy as np

from agents.voice_security_agent import (
    AcousticGraphAttention,
    KANLinearLayer,
    VoiceSecurityAgent,
    VoiceSecurityResult,
)


def test_kan_layer_forward():
    layer = KANLinearLayer(in_features=16, out_features=8, grid_size=5, spline_order=3)
    x = np.random.normal(0, 1, 16)
    out = layer.forward(x)
    assert out.shape == (8,)
    assert not np.isnan(out).any()


def test_graph_attention_forward():
    gat = AcousticGraphAttention(feature_dim=32, heads=2)
    # 20 frames with 32 features
    frames = np.random.normal(0, 1, (20, 32))
    out = gat.forward(frames)
    assert out.shape == (32,)
    assert not np.isnan(out).any()


def test_voice_security_genuine_voice():
    agent = VoiceSecurityAgent(authenticity_threshold=0.80)
    result = agent.evaluate_voice(audio_data=None, is_simulated_spoof=False)
    assert isinstance(result, VoiceSecurityResult)
    assert result.is_bona_fide is True
    assert result.authenticity_score >= 0.80
    assert result.spoof_probability <= 0.20
    assert result.verdict == "VERIFIED_GENUINE"


def test_voice_security_detects_spoof():
    agent = VoiceSecurityAgent(authenticity_threshold=0.80)
    result = agent.evaluate_voice(audio_data=None, is_simulated_spoof=True)
    assert isinstance(result, VoiceSecurityResult)
    assert result.is_bona_fide is False
    assert result.authenticity_score < 0.80
    assert result.verdict == "REJECTED_SYNTHETIC_DEEPFAKE"
    assert len(result.detected_artifacts) > 0
