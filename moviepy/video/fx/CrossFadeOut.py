from moviepy.Clip import Clip
from moviepy.Effect import Effect
from dataclasses import dataclass

from moviepy.video.fx.FadeOut import FadeOut


@dataclass
class CrossFadeOut(Effect):
    """Makes the clip disappear progressively, over ``duration`` seconds.
    Only works when the clip is included in a CompositeVideoClip.
    """

    duration: float

    def apply(self, clip: Clip) -> Clip:
        if clip.duration is None:
            raise ValueError("Attribute 'duration' not set")

        if clip.mask is None:
            clip = clip.with_add_mask()

        clip.mask.duration = clip.duration
        clip.mask = clip.mask.with_effects([FadeOut(self.duration)])

        return clip
