"""
Unit tests for KIM Chief Female AI Strategist & Voice Agent.
Zero emojis.
"""
import os
import pytest
from agents.kim_voice_agent import KimResponse, KimVoiceAgent, kim_voice_agent, synthesize_female_speech_wav


def test_kim_female_speech_synthesis():
    wav_path = synthesize_female_speech_wav("Hello, this is Kim verifying speech output.")
    assert wav_path is not None
    assert os.path.exists(wav_path)
    assert os.path.getsize(wav_path) > 1000


def test_kim_chart_command():
    resp = kim_voice_agent.process_command("Can you pull up the US 30-year chart in TradingView?")
    assert isinstance(resp, KimResponse)
    assert resp.visual_action == "chart"
    assert resp.target_symbol == "US30Y"
    assert "Treasury yield" in resp.spoken_script or "bond market" in resp.spoken_script


def test_kim_fedwatch_command():
    resp = kim_voice_agent.process_command("So what is the Fed going to do this Wednesday? Can you check?")
    assert isinstance(resp, KimResponse)
    assert resp.visual_action == "fedwatch"
    assert "futures market" in resp.spoken_script


def test_kim_heatmap_command():
    resp = kim_voice_agent.process_command("Can you check the market heat map?")
    assert isinstance(resp, KimResponse)
    assert resp.visual_action == "heatmap"
    assert "heat map" in resp.spoken_script or "market" in resp.spoken_script


def test_kim_macro_correlation():
    resp = kim_voice_agent.process_command("What does this mean for the market? Oil is the reason, tech is the victim.")
    assert isinstance(resp, KimResponse)
    assert resp.visual_action == "correlation"
    assert "tech is the victim" in resp.spoken_script or "Oil" in resp.spoken_script


def test_kim_voice_security_spoof_lock():
    from agents.voice_security_agent import voice_security_agent, VoiceSecurityResult
    fake_audio = b"\x00\x00" * 64
    orig_eval = voice_security_agent.evaluate_voice
    try:
        voice_security_agent.evaluate_voice = lambda *args, **kwargs: VoiceSecurityResult(
            is_bona_fide=False,
            authenticity_score=0.25,
            spoof_probability=0.75,
            spectral_jitter=0.12,
            vocoder_artifact_score=11.2,
            temporal_discontinuity=2.4,
            detected_artifacts=["Phase Discontinuity", "Vocoder Inversion"],
            verdict="REJECTED_SYNTHETIC_DEEPFAKE",
        )
        resp = kim_voice_agent.process_command("Execute unauthorized wire", audio_data=fake_audio)
        assert resp.voice_security_status == "REJECTED_SYNTHETIC_DEEPFAKE"
        assert "Synthetic speech artifacts" in resp.spoken_script
    finally:
        voice_security_agent.evaluate_voice = orig_eval


def test_kim_dynamic_non_repeating_responses():
    """
    Verifies that Kim never repeats a static canned sentence when the user changes questions.
    Each distinct query must produce a bespoke, tailored response backed by real tool telemetry.
    """
    old_canned_fallback = "On it, boss. Tracking 16 key entities."

    r_btc = kim_voice_agent.process_command("What is your quantitative stance on Bitcoin?")
    r_news = kim_voice_agent.process_command("What is the latest breaking news on the internet?")
    r_rates = kim_voice_agent.process_command("What are 10-year Treasury yields doing right now?")

    assert old_canned_fallback not in r_btc.spoken_script
    assert old_canned_fallback not in r_news.spoken_script
    assert old_canned_fallback not in r_rates.spoken_script

    # All three spoken scripts must be different from each other
    assert r_btc.spoken_script != r_news.spoken_script
    assert r_news.spoken_script != r_rates.spoken_script
    assert r_btc.spoken_script != r_rates.spoken_script

    # Tool traces must reflect dynamic tool execution
    assert len(r_btc.tool_trace) > 0
    assert len(r_news.tool_trace) > 0
    assert len(r_rates.tool_trace) > 0
