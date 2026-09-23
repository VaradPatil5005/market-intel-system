"""Unit tests for FRIDAY Master Voice & Multimodal Command Agent."""
from __future__ import annotations

from agents.friday_voice_agent import FridayResponse, FridayVoiceAgent


def test_friday_chart_command_routing():
    agent = FridayVoiceAgent()
    resp = agent.process_command("Can you pull up the US 30-year chart in TradingView?")
    assert isinstance(resp, FridayResponse)
    assert resp.visual_action == "chart"
    assert resp.target_symbol == "US30Y"
    assert "Treasury yield" in resp.spoken_script or "bond market" in resp.spoken_script
    assert "TREASURY YIELD" in resp.teleprompter_text or "Bond" in resp.teleprompter_text


def test_friday_fedwatch_command_routing():
    agent = FridayVoiceAgent()
    resp = agent.process_command("So what is the Fed going to do this Wednesday? Can you check?")
    assert isinstance(resp, FridayResponse)
    assert resp.visual_action == "fedwatch"
    assert "futures market" in resp.spoken_script
    assert "CME FEDWATCH" in resp.teleprompter_text or "FedWatch" in resp.teleprompter_text


def test_friday_heatmap_command_routing():
    agent = FridayVoiceAgent()
    resp = agent.process_command("Can you check the market heat map?")
    assert isinstance(resp, FridayResponse)
    assert resp.visual_action == "heatmap"
    assert "heat map" in resp.spoken_script or "market" in resp.spoken_script
    assert "SECTOR TREEMAP" in resp.teleprompter_text or "Heatmap" in resp.teleprompter_text


def test_friday_macro_correlation_routing():
    agent = FridayVoiceAgent()
    resp = agent.process_command("What does this mean for the market? Oil is the reason, tech is the victim.")
    assert isinstance(resp, FridayResponse)
    assert resp.visual_action == "correlation"
    assert "tech is the victim" in resp.spoken_script or "Oil" in resp.spoken_script
    assert "CROSS-ASSET" in resp.teleprompter_text or "Cross-Asset" in resp.teleprompter_text


def test_friday_voice_security_rejection_on_spoof():
    agent = FridayVoiceAgent()
    from agents.voice_security_agent import voice_security_agent
    # Simulate a spoof audio buffer
    fake_audio = b"\x00\x00" * 32
    # Mock evaluate_voice to return spoof
    orig_eval = voice_security_agent.evaluate_voice
    try:
        from agents.voice_security_agent import VoiceSecurityResult
        voice_security_agent.evaluate_voice = lambda *args, **kwargs: VoiceSecurityResult(
            is_bona_fide=False,
            authenticity_score=0.32,
            spoof_probability=0.68,
            spectral_jitter=0.08,
            vocoder_artifact_score=9.5,
            temporal_discontinuity=1.8,
            detected_artifacts=["Vocoder Phase Inconsistency"],
            verdict="REJECTED_SYNTHETIC_DEEPFAKE",
        )
        resp = agent.process_command("Execute trade", audio_data=fake_audio)
        assert resp.voice_security_status == "REJECTED_SYNTHETIC_DEEPFAKE"
        assert "Synthetic speech artifacts" in resp.spoken_script
    finally:
        voice_security_agent.evaluate_voice = orig_eval
