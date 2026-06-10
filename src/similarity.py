import numpy as np
from PIL import Image
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

_face_analyzer = None


def _get_analyzer():
    global _face_analyzer
    if _face_analyzer is None:
        try:
            import insightface
            _face_analyzer = insightface.app.FaceAnalysis(
                name="buffalo_l",
                providers=["CPUExecutionProvider"],
            )
            _face_analyzer.prepare(ctx_id=-1)
        except Exception as e:
            logger.warning(f"InsightFace failed to initialize: {e}")
            return None
    return _face_analyzer


def compute_face_similarity(ref_image: Image.Image, gen_image: Image.Image) -> float | None:
    analyzer = _get_analyzer()
    if analyzer is None:
        return None

    ref_array = np.array(ref_image.convert("RGB"))
    gen_array = np.array(gen_image.convert("RGB"))

    ref_faces = analyzer.get(ref_array)
    gen_faces = analyzer.get(gen_array)

    if not ref_faces:
        logger.warning("No face found in reference image")
        return None

    ref_embedding = ref_faces[0].normed_embedding

    if not gen_faces:
        logger.warning("No face found in generated image")
        return 0.0

    gen_embedding = gen_faces[0].normed_embedding

    similarity = float(np.dot(ref_embedding, gen_embedding))
    return round(similarity, 4)


SIMILARITY_THRESHOLDS = {
    "accept": 0.90,
    "warning": 0.85,
    "regenerate": 0.85,
}


def evaluate_similarity(score: float | None) -> str:
    if score is None:
        return "unknown"
    if score >= SIMILARITY_THRESHOLDS["accept"]:
        return "accept"
    if score >= SIMILARITY_THRESHOLDS["warning"]:
        return "warning"
    return "low"
