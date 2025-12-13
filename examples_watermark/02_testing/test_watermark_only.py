"""
AgentMark Watermark Test - No API Required

This lightweight test validates the watermark embedding and extraction
without requiring OpenAI API or actual agent simulation.

Note: This test requires full OASIS installation. For standalone testing
without dependencies, use test_watermark_standalone.py instead.
"""

import os
import sys
import datetime
import uuid

# 修复路径：从 examples_watermark/02_testing/ 回到项目根目录
# 当前位置: oasis/examples_watermark/02_testing/test_watermark_only.py
# 需要回到: oasis/ (项目根目录)
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, parent_dir)

try:
    from oasis.watermark import WatermarkManager
except ImportError as e:
    print(f"❌ Failed to import oasis.watermark: {e}")
    print("\n💡 Tip: Use test_watermark_standalone.py for testing without full OASIS installation")
    print("   Usage: python examples/test_watermark_standalone.py")
    sys.exit(1)


def test_watermark_embedding_extraction():
    """
    Test watermark embedding and extraction without LLM
    """
    print("=" * 80)
    print("AgentMark Watermark Test (No API Required)")
    print("=" * 80)
    
    # Step 1: Initialize
    print("\n📋 Step 1: Initialize WatermarkManager")
    payload = "11001101"  # 8-bit message
    
    # 使用独立的输出目录，避免多次运行/并发导致日志混淆
    from pathlib import Path
    project_root = Path(__file__).parent.parent.parent
    run_id = datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:8]
    log_dir_path = project_root / "outputs" / "logs" / "watermark" / "tests" / run_id
    log_dir_path.mkdir(parents=True, exist_ok=True)
    log_dir = str(log_dir_path)
    
    wm = WatermarkManager(
        enabled=True,
        mode="full",
        config={
            "payload_bit_length": 8,
            "ecc_method": "parity",
            "embedding_strategy": "cyclic"
        },
        bit_stream=payload,
        log_dir=log_dir
    )
    
    print(f"✅ Payload: {payload}")
    print(f"✅ Encoded bit stream: {wm.bit_stream} ({len(wm.bit_stream)} bits)")
    
    # Step 2: Simulate watermark embedding
    print("\n📋 Step 2: Simulate Watermark Embedding")
    
    # 循环采样直到至少完成 1 个完整编码块（例如 parity: 9 bits）
    test_behaviors = [
        {"like": 0.3, "post": 0.2, "comment": 0.5},
        {"like": 0.4, "post": 0.3, "comment": 0.3},
        {"like": 0.2, "post": 0.5, "comment": 0.3},
        {"like": 0.35, "post": 0.35, "comment": 0.3},
        {"like": 0.3, "post": 0.4, "comment": 0.3},
    ]
    
    context = ""
    expected_encoded_len = len(wm.bit_stream)
    max_rounds = 80

    for round_num in range(max_rounds):
        probs = test_behaviors[round_num % len(test_behaviors)]
        selected, targets, bits, ctx = wm.sample_behavior_watermark(
            probabilities=probs,
            round_num=round_num,
            context_for_key=context
        )
        
        print(f"Round {round_num}: Selected '{selected}', embedded {bits} bits")
        context = ctx  # Update context for next round

        if wm.get_statistics()["bits_embedded"] >= expected_encoded_len:
            break
    
    # Step 3: Show statistics
    print("\n📋 Step 3: Statistics")
    stats = wm.get_statistics()
    print(f"✅ Watermarked actions: {stats['watermarked_actions']}")
    print(f"✅ Bits embedded: {stats['bits_embedded']}")
    print(f"✅ Log file: {stats['log_file']}")
    
    # Step 4: Extract watermark
    print("\n📋 Step 4: Extract and Verify")
    
    extracted_bits, extraction_stats = wm.extract_watermark_from_log()
    
    print(f"📊 Extraction results:")
    print(f"   Actions processed: {extraction_stats.get('actions_processed')}")
    print(f"   Extracted: {extraction_stats['extracted_bit_stream']}")
    print(f"   Decoded: {extraction_stats['decoded_payload']}")
    print(f"   Valid: {extraction_stats['valid']}")
    
    # Step 5: Verify
    print("\n📋 Step 5: Verification")
    print(f"   Original: {payload}")
    print(f"   Decoded:  {extraction_stats['decoded_payload']}")
    
    decoded = extraction_stats.get('decoded_payload', '')
    if decoded[:len(payload)] == payload and extraction_stats.get('valid'):
        print(f"\n   ✅ SUCCESS! Watermark verified!")
        print(f"   🎉 All components working correctly!")
        return True
    else:
        print(f"\n   ❌ FAILED! Verification error")
        if extraction_stats.get("error"):
            print(f"   Error: {extraction_stats.get('error')}")
        return False


def test_different_payloads():
    """
    Test with different payloads
    """
    print("\n\n" + "=" * 80)
    print("Testing Different Payloads")
    print("=" * 80)
    
    test_cases = [
        "00000000",  # All zeros
        "11111111",  # All ones
        "10101010",  # Alternating
        "01010101",  # Alternating inverse
        "11001100",  # Pattern
    ]
    
    results = []
    
    from pathlib import Path
    project_root = Path(__file__).parent.parent.parent
    run_id = datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:8]
    base_log_dir = project_root / "outputs" / "logs" / "watermark" / "tests" / f"payloads-{run_id}"
    base_log_dir.mkdir(parents=True, exist_ok=True)

    for payload in test_cases:
        from pathlib import Path
        # 每个 payload 使用独立目录，避免同一秒创建多个 WatermarkManager 导致日志文件名冲突
        log_dir_path = base_log_dir / payload
        log_dir_path.mkdir(parents=True, exist_ok=True)
        log_dir = str(log_dir_path)
        
        wm = WatermarkManager(
            enabled=True,
            config={"payload_bit_length": 8, "ecc_method": "parity"},
            bit_stream=payload,
            log_dir=log_dir
        )
        
        # Embed until at least one complete encoded block is available
        expected_encoded_len = len(wm.bit_stream)
        max_rounds = 120
        for i in range(max_rounds):
            wm.sample_behavior_watermark(
                probabilities={"a": 0.3, "b": 0.3, "c": 0.4},
                round_num=i,
                context_for_key=""
            )
            if wm.get_statistics()["bits_embedded"] >= expected_encoded_len:
                break
        
        # Extract
        _, stats = wm.extract_watermark_from_log()
        
        decoded = stats.get('decoded_payload', '')
        success = (decoded[:len(payload)] == payload and stats.get('valid'))
        results.append((payload, success))
        
        status = "✅" if success else "❌"
        print(f"{status} Payload {payload}: {'PASS' if success else 'FAIL'}")
    
    # Summary
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"\n📊 Results: {passed}/{total} passed ({passed/total*100:.1f}%)")
    
    return all(success for _, success in results)


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║                                                                  ║
    ║     AgentMark Watermark Validation Test (No API Required)       ║
    ║                                                                  ║
    ║  This test validates watermark embedding and extraction         ║
    ║  without requiring OpenAI API or LLM calls.                     ║
    ║                                                                  ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        # Test 1: Basic watermark test
        success1 = test_watermark_embedding_extraction()
        
        # Test 2: Different payloads
        success2 = test_different_payloads()
        
        print("\n" + "=" * 80)
        if success1 and success2:
            print("🎉 ALL TESTS PASSED!")
            print("AgentMark watermark system is working correctly!")
        else:
            print("⚠️  SOME TESTS FAILED")
            print("Please check the logs for details")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
