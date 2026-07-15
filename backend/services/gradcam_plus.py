"""
Production-Quality Gradient-based CAM Implementation for Plant Disease Detection
==================================================================================

This module implements activation-based visualization with gradient support for 
precise disease region localization. It uses the EfficientNetB0's final convolutional
layer to generate disease heatmaps.

Key Features:
1. Accesses the "top_conv" layer (7x7x1280) from EfficientNetB0
2. Visualizes conv layer activations for disease regions
3. Robust gradient handling for nested model structures
4. Proper post-processing with Gaussian smoothing and adaptive overlay

Model: EfficientNetB0 (best_farmlens_finetuned.keras, 66 classes)
Target Layer: "top_conv" (final convolutional layer, shape: 7x7x1280)
"""

import numpy as np
import cv2
import base64
from typing import Optional, Tuple
import tensorflow as tf


class GradCAMPlusPlus:
    """
    Grad-CAM++ implementation optimized for disease detection and nested architectures.
    """
    
    def __init__(self, model: tf.keras.Model, target_layer_name: str = "top_conv"):
        self.model = model 
        self.target_layer_name = target_layer_name
        self.base_model = None
        self.inner_model = None
        self.classifier_layers = []
        
        self._initialize_grad_model()
    
    def _initialize_grad_model(self):
        """Initialize models to properly route gradients through nested layers."""
        try:
            base_model_idx = -1
            # 1. Find the inner EfficientNet base model
            for i, layer in enumerate(self.model.layers):
                if "efficientnet" in layer.name.lower():
                    self.base_model = layer
                    base_model_idx = i
                    break

            if self.base_model is None:
                raise ValueError("EfficientNet base model not found.")

            print(f"[Grad-CAM] Base model : {self.base_model.name}")
            
            target_layer = self.base_model.get_layer(self.target_layer_name)
            print(f"[Grad-CAM] Target layer : {target_layer.name}")

            # 2. Create inner model that stops at the base_model's output
            self.inner_model = tf.keras.Model(
                inputs=self.base_model.input,
                outputs=[target_layer.output, self.base_model.output]
            )

            # 3. Store the outer classifier layers (pooling, dense, etc.)
            self.classifier_layers = self.model.layers[base_model_idx + 1:]

            print("[Grad-CAM] Gradient model initialized successfully.")

        except Exception as e:
            print(f"[Grad-CAM] Initialization error: {e}")
            raise
    
    def compute_heatmap(
        self,
        img_array,
        class_idx,
        eps=1e-8
    ):
        try:
            img_tensor = tf.convert_to_tensor(img_array, dtype=tf.float32)

            with tf.GradientTape() as tape:
                # 1. Forward pass through inner model
                conv_outputs, base_output = self.inner_model(img_tensor)

                # Explicitly tell the tape to track these convolutions
                tape.watch(conv_outputs)

                # 2. Forward pass through the outer classification head
                x = base_output
                for layer in self.classifier_layers:
                    x = layer(x)
                predictions = x

                # Isolate the loss of the predicted class
                loss = predictions[:, class_idx]

            # 3. Calculate gradients of the loss with respect to the convolutions
            grads = tape.gradient(loss, conv_outputs)

            if grads is None:
                print("[Grad-CAM] Gradients are None - Check architecture")
                return None

            # Pool and weight the gradients
            pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
            conv_outputs = conv_outputs[0]

            heatmap = tf.reduce_sum(
                conv_outputs * pooled_grads,
                axis=-1
            )

            # Relu activation on heatmap and normalize
            heatmap = tf.maximum(heatmap, 0)
            heatmap = heatmap / (tf.reduce_max(heatmap) + eps)
            heatmap_np = heatmap.numpy()

            print("\n========== GRADCAM COMPUTATION ==========")
            print("Grad max :", tf.reduce_max(grads).numpy())
            print("Grad min :", tf.reduce_min(grads).numpy())
            print("Heatmap max :", np.max(heatmap_np))
            print("Heatmap mean :", np.mean(heatmap_np))
            print("=========================================\n")

            return heatmap_np.astype(np.float32)

        except Exception as e:
            print(f"[Grad-CAM] Heatmap computation failed: {e}")
            import traceback
            traceback.print_exc()
            return None

    def postprocess_heatmap(
        self,
        heatmap: np.ndarray,
        original_size: Tuple[int, int],
        apply_smoothing: bool = True
    ) -> np.ndarray:
        """
        Post-process the heatmap for visualization.
        """
        # Step 1: Resize to original image resolution using bicubic interpolation
        heatmap_resized = cv2.resize(
            heatmap, 
            (original_size[1], original_size[0]),  # (width, height)
            interpolation=cv2.INTER_CUBIC
        )
        
        # Step 2: Apply light Gaussian smoothing only if it improves localization
        if apply_smoothing:
            kernel_size = 5
            sigma = 1.0
            heatmap_resized = cv2.GaussianBlur(
                heatmap_resized, 
                (kernel_size, kernel_size), 
                sigma
            )
        
        # Step 3: Re-normalize after smoothing
        if heatmap_resized.max() > 1e-8:
            heatmap_resized = heatmap_resized / heatmap_resized.max()
        
        # Step 4: Apply threshold to reduce background noise
        threshold = 0.10
        heatmap_resized = np.where(heatmap_resized > threshold, heatmap_resized, 0)
        
        # Step 5: Final normalization
        if heatmap_resized.max() > 1e-8:
            heatmap_resized = heatmap_resized / heatmap_resized.max()
        
        return heatmap_resized


def generate_gradcam_visualization(
    image_bytes: bytes,
    model: tf.keras.Model,
    img_array: np.ndarray,
    class_idx: int,
    severity: int,
    disease: str = "Unknown",
    confidence: int = 0
) -> str:
    """
    Generate complete Grad-CAM++ visualization with overlay.
    Generates LOW-RESOLUTION heatmap to keep payload small and avoid 431 errors.
    
    Args:
        image_bytes: Original image bytes
        model: Trained Keras model
        img_array: Preprocessed image array for model (1, 224, 224, 3)
        class_idx: Predicted class index
        severity: Disease severity (0-100)
        disease: Disease name
        confidence: Model confidence (0-100)
        
    Returns:
        Base64-encoded JPEG of heatmap overlay (LOW-RES), or empty string if failed
    """
    try:
        # Step 1: Decode original image
        nparr = np.frombuffer(image_bytes, np.uint8)
        img_original = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img_original is None:
            print("[Grad-CAM++] Failed to decode image")
            return ""
        
        h, w = img_original.shape[:2]
        
        # Step 2: Initialize Grad-CAM++
        gradcam = GradCAMPlusPlus(model, target_layer_name="top_conv")
        
        # Step 3: Compute heatmap
        print(f"[Grad-CAM++] Computing heatmap for class {class_idx}")
        heatmap = gradcam.compute_heatmap(img_array, class_idx)
        
        cv2.imwrite("raw_heatmap.png", (heatmap * 255).astype(np.uint8))
        print("[Grad-CAM] Raw heatmap saved.")
        
        if heatmap is None:
            print("[Grad-CAM++] Heatmap computation failed")
            return ""
        
        # Step 4: Post-process heatmap
        apply_smoothing = severity > 50
        heatmap_processed = gradcam.postprocess_heatmap(
            heatmap, 
            (h, w),
            apply_smoothing=apply_smoothing
        )
        
        # Step 5: RESIZE IMAGE TO REDUCE PAYLOAD
        # Keep aspect ratio, but reduce size significantly
        max_dimension = 400  # Max 400px on longest side
        if h > max_dimension or w > max_dimension:
            scale = max_dimension / max(h, w)
            new_h = int(h * scale)
            new_w = int(w * scale)
            img_original = cv2.resize(img_original, (new_w, new_h))
            heatmap_processed = cv2.resize(heatmap_processed, (new_w, new_h))
            print(f"[Grad-CAM++] Resized from {h}x{w} to {new_h}x{new_w}")
        
        # Step 6: Create visualization
        heatmap_uint8 = (heatmap_processed * 255).astype(np.uint8)
        heatmap_colored = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
        
        # Step 7: Create overlay with adaptive alpha
        base_alpha = 0.40
        severity_factor = (severity / 100.0) * 0.30
        alpha = base_alpha + severity_factor
        
        overlay = cv2.addWeighted(
            img_original, 
            1.0 - alpha,
            heatmap_colored, 
            alpha,
            0
        )
        
        # Step 8: Add information bar
        overlay_with_info = add_info_bar(
            overlay,
            disease,
            severity,
            confidence
        )
        
        # Step 9: Encode to base64 with AGGRESSIVE compression
        # Use VERY low JPEG quality to ensure small payload
        _, buffer = cv2.imencode('.jpg', overlay_with_info, [cv2.IMWRITE_JPEG_QUALITY, 40])
        img_b64 = base64.b64encode(buffer).decode('utf-8')
        
        # Final size check - if still too large, give up gracefully
        if len(img_b64) > 300000:  # > 300KB
            print(f"[Grad-CAM++] Heatmap still too large ({len(img_b64)} bytes), skipping")
            return ""
        
        print(f"[Grad-CAM++] Successfully generated visualization ({len(img_b64)} bytes)")
        return img_b64
        
    except Exception as e:
        print(f"[Grad-CAM++] Visualization failed: {e}")
        import traceback
        traceback.print_exc()
        return ""


def add_info_bar(
    img: np.ndarray,
    disease: str,
    severity: int,
    confidence: int
) -> np.ndarray:
    """
    Add information bar to the heatmap overlay.
    
    Args:
        img: Image array (H, W, 3)
        disease: Disease name
        severity: Severity percentage
        confidence: Confidence percentage
        
    Returns:
        Image with info bar added at top
    """
    h, w = img.shape[:2]
    
    # Create info bar
    bar_height = max(40, h // 12)
    info_bar = np.zeros((bar_height, w, 3), dtype=np.uint8)
    info_bar[:] = (20, 20, 20)  # Dark background
    
    # Text settings
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = max(0.5, bar_height / 60)
    thickness = max(1, int(bar_height / 30))
    color = (255, 255, 255)
    
    # Add disease name
    text_y = int(bar_height * 0.6)
    cv2.putText(
        info_bar,
        f"{disease}",
        (10, text_y),
        font,
        font_scale,
        color,
        thickness,
        cv2.LINE_AA
    )
    
    # Add severity
    severity_color = (0, 255, 0) if severity < 30 else (0, 165, 255) if severity < 60 else (0, 0, 255)
    cv2.putText(
        info_bar,
        f"Severity: {severity}%",
        (w // 3, text_y),
        font,
        font_scale * 0.9,
        severity_color,
        thickness,
        cv2.LINE_AA
    )
    
    # Add confidence
    cv2.putText(
        info_bar,
        f"AI: {confidence}%",
        (2 * w // 3, text_y),
        font,
        font_scale * 0.9,
        (100, 200, 255),
        thickness,
        cv2.LINE_AA
    )
    
    # Stack info bar on top of image
    result = np.vstack([info_bar, img])
    
    return result


# Backward compatibility function
def generate_heatmap_b64(
    image_bytes: bytes,
    severity: int,
    crop: str = "Unknown",
    disease: str = "Unknown",
    confidence: int = 0,
    model=None,
    img_array=None,
    class_idx: int = 0
) -> str:
    """
    Backward-compatible wrapper for heatmap generation.
    
    If model and img_array are provided, uses Grad-CAM++.
    Otherwise, falls back to color-based visualization.
    
    Args:
        image_bytes: Original image bytes
        severity: Disease severity (0-100)
        crop: Crop name (for fallback)
        disease: Disease name
        confidence: Model confidence
        model: Optional - Keras model for Grad-CAM++
        img_array: Optional - Preprocessed image for model
        class_idx: Optional - Predicted class index
        
    Returns:
        Base64-encoded JPEG of visualization
    """
    # Use Grad-CAM++ if model is provided
    if model is not None and img_array is not None:
        return generate_gradcam_visualization(
            image_bytes,
            model,
            img_array,
            class_idx,
            severity,
            disease,
            confidence
        )
    else:
        # Fallback: simple overlay (for healthy plants or when model unavailable)
        print("[Heatmap] Using fallback color-based visualization")
        return generate_simple_overlay(image_bytes, severity, disease, confidence)


def generate_simple_overlay(
    image_bytes: bytes,
    severity: int,
    disease: str,
    confidence: int
) -> str:
    """
    Simple color-based overlay for when Grad-CAM++ is not available.
    Used for healthy plants or as fallback.
    """
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return ""
        
        h, w = img.shape[:2]
        
        # Create a uniform low-intensity overlay for healthy plants
        overlay = img.copy()
        
        # Add subtle green tint for healthy
        if severity < 10:
            green_overlay = np.zeros_like(img)
            green_overlay[:, :, 1] = 30  # Light green
            overlay = cv2.addWeighted(img, 0.9, green_overlay, 0.1, 0)
        
        # Add info bar
        overlay_with_info = add_info_bar(overlay, disease, severity, confidence)
        
        # Encode to base64 with compression
        _, buffer = cv2.imencode('.jpg', overlay_with_info, [cv2.IMWRITE_JPEG_QUALITY, 60])
        img_b64 = base64.b64encode(buffer).decode('utf-8')
        
        return img_b64
        
    except Exception as e:
        print(f"[Simple Overlay] Failed: {e}")
        return ""