from .core import ElementData, Element
from .elements import StyleBoxData


popup = StyleBoxData(...)

popup_shaking = popup.add_keyframe(
    marker=NotificationState.ALERT,
    animation=ShakeAnimation(),
    data=None # This can be implicit, Basically don't change anything just shake
)

popup_shaking.add_keyframe(
    marker=ElementState.HOVERED,
    animation=NoAnimation(), # If it was None it would still shake
    data=StyleBoxData(
        border_color = (255, 255, 255, 255)
    ) # Add glow but don't change anything else
)

popup_shaking.add_keyframe(
    marker=ElementState.CLICKED,
    animation=PulseAnimation(),
    data=None,  # This can be implicit, Basically don't change anything but darken the base color
)