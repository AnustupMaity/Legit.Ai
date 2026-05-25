from __future__ import annotations

import io
import tempfile
import os
from typing import List

import cv2
import numpy as np
from PIL import Image

import config
from backend.model.image_detector import detect_image


def extract_frames_from_video(video_bytes: bytes, frame_interval: int = 30) -> list[bytes]:
    """
    Extract frames from video at regular intervals.
    
    Args:
        video_bytes: Video file content
        frame_interval: Extract every Nth frame (default: 30 frames ≈ 1 second at 30fps)
    
    Returns:
        List of frame images as bytes
    """
    frames = []
    
    # Save video to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
        temp_file.write(video_bytes)
        temp_file.flush()
        temp_path = temp_file.name
    
    try:
        # Open video file
        cap = cv2.VideoCapture(temp_path)
        
        if not cap.isOpened():
            raise ValueError("Could not open video file")
        
        frame_count = 0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        # Calculate how many frames to extract (max 20 for performance)
        max_frames = 20
        frames_to_extract = min(max_frames, total_frames // frame_interval)
        
        if frames_to_extract == 0:
            # Extract at least first frame
            frames_to_extract = 1
            frame_interval = 1
        
        while len(frames) < frames_to_extract:
            ret, frame = cap.read()
            
            if not ret:
                break
            
            if frame_count % frame_interval == 0:
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Convert to PIL Image and then bytes
                pil_image = Image.fromarray(frame_rgb)
                img_byte_arr = io.BytesIO()
                pil_image.save(img_byte_arr, format='JPEG')
                frame_bytes = img_byte_arr.getvalue()
                frames.append(frame_bytes)
            
            frame_count += 1
        
        cap.release()
        
    except Exception as exc:
        print(f"Video processing failed: {exc}")
    finally:
        # Clean up temp file
        try:
            os.unlink(temp_path)
        except:
            pass
    
    return frames


def detect_video(video_bytes: bytes, filename: str | None = None) -> dict:
    """
    Detect AI-generated or manipulated content in video by analyzing frames.
    
    Args:
        video_bytes: Video file content
        filename: Original filename
    
    Returns:
        Detection result with frame-by-frame analysis
    """
    try:
        # Extract frames from video
        frames = extract_frames_from_video(video_bytes)
        
        if not frames:
            return {
                "fake": False,
                "confidence": 0.0,
                "reason": "Could not extract frames from video",
                "model": "video-processor",
                "labels": [],
                "frame_count": 0,
                "frame_results": [],
            }
        
        # Analyze each frame
        frame_results = []
        fake_frames = 0
        total_confidence = 0.0
        
        for i, frame_bytes in enumerate(frames):
            try:
                frame_result = detect_image(frame_bytes, f"{filename}_frame_{i}")
                frame_results.append({
                    "frame_number": i,
                    "fake": frame_result.get("fake", False),
                    "confidence": frame_result.get("confidence", 0.0),
                    "reason": frame_result.get("reason", ""),
                })
                
                if frame_result.get("fake"):
                    fake_frames += 1
                total_confidence += frame_result.get("confidence", 0.0)
                
            except Exception as exc:
                print(f"Frame {i} analysis failed: {exc}")
                frame_results.append({
                    "frame_number": i,
                    "fake": False,
                    "confidence": 0.0,
                    "reason": f"Analysis failed: {str(exc)}",
                })
        
        # Calculate overall result
        total_frames = len(frames)
        fake_ratio = fake_frames / total_frames if total_frames > 0 else 0
        avg_confidence = total_confidence / total_frames if total_frames > 0 else 0
        
        # Video is considered fake if >40% of frames are flagged
        is_fake = fake_ratio > 0.4
        overall_confidence = max(avg_confidence, fake_ratio * 100)
        
        reason = f"Analyzed {total_frames} frames. {fake_frames} flagged as fake ({fake_ratio:.1%}). "
        if is_fake:
            reason += f"Video likely contains AI-generated or manipulated content."
        else:
            reason += f"Video appears to be authentic."
        
        return {
            "fake": is_fake,
            "confidence": round(overall_confidence, 1),
            "reason": reason,
            "model": "video-frame-analyzer",
            "labels": [
                {"label": "video", "score": 1.0},
                {"label": f"frames-analyzed:{total_frames}", "score": 1.0},
                {"label": f"fake-frames:{fake_frames}", "score": fake_ratio},
            ],
            "frame_count": total_frames,
            "fake_frame_count": fake_frames,
            "frame_results": frame_results,
        }
        
    except Exception as exc:
        return {
            "fake": False,
            "confidence": 0.0,
            "reason": f"Video analysis failed: {str(exc)}",
            "model": "video-processor",
            "labels": [],
            "frame_count": 0,
            "frame_results": [],
        }
