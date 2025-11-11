"""
AgentMark Watermark Test - No API Required

This lightweight test validates the watermark embedding and extraction
without requiring OpenAI API or actual agent simulation.

Note: This test requires full OASIS installation. For standalone testing
without dependencies, use test_watermark_standalone.py instead.
"""

import os
import sys

# 修复路径：从 examples_watermark/03_testing/ 回到项目根目录
# 当前位置: oasis/examples_watermark/03_testing/test_watermark_only.py
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
    
    # 使用统一的输出目录
    from pathlib import Path
    project_root = Path(__file__).parent.parent.parent
    log_dir = str(project_root / "outputs" / "logs" / "watermark" / "2025-11")
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
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
    
    # Simulate 5 rounds of behavior sampling
    test_behaviors = [
        {"like": 0.3, "post": 0.2, "comment": 0.5},
        {"like": 0.4, "post": 0.3, "comment": 0.3},
        {"like": 0.2, "post": 0.5, "comment": 0.3},
        {"like": 0.35, "post": 0.35, "comment": 0.3},
        {"like": 0.3, "post": 0.4, "comment": 0.3},
    ]
    
    context = ""
    for round_num, probs in enumerate(test_behaviors):
        selected, targets, bits, ctx = wm.sample_behavior_watermark(
            probabilities=probs,
            round_num=round_num,
            context_for_key=context
        )
        
        print(f"Round {round_num}: Selected '{selected}', embedded {bits} bits")
        context = ctx  # Update context for next round
    
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
    print(f"   Rounds parsed: {extraction_stats['rounds_parsed']}")
    print(f"   Extracted: {extraction_stats['extracted_bit_stream']}")
    print(f"   Decoded: {extraction_stats['decoded_payload']}")
    print(f"   Valid: {extraction_stats['valid']}")
    
    # Step 5: Verify
    print("\n📋 Step 5: Verification")
    print(f"   Original: {payload}")
    print(f"   Decoded:  {extraction_stats['decoded_payload']}")
    
    if extraction_stats['decoded_payload'] == payload and extraction_stats['valid']:
        print(f"\n   ✅ SUCCESS! Watermark verified!")
        print(f"   🎉 All components working correctly!")
        return True
    else:
        print(f"\n   ❌ FAILED! Verification error")
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
    
    for payload in test_cases:
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent
        log_dir = str(project_root / "outputs" / "logs" / "watermark" / "2025-11")
        
        wm = WatermarkManager(
            enabled=True,
            config={"payload_bit_length": 8, "ecc_method": "parity"},
            bit_stream=payload,
            log_dir=log_dir
        )
        
        # Embed
        for i in range(5):
            wm.sample_behavior_watermark(
                probabilities={"a": 0.3, "b": 0.3, "c": 0.4},
                round_num=i,
                context_for_key=""
            )
        
        # Extract
        _, stats = wm.extract_watermark_from_log()
        
        success = (stats['decoded_payload'] == payload and stats['valid'])
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
