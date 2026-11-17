"""Pure sizing calculations for the existing preview and resize handle."""


def legacy_drag_height(height, pointer_delta, minimum):
    return max(minimum, height + pointer_delta)


def preview_limit(viewport_height, chrome_height):
    return max(60, viewport_height - max(0, chrome_height))


class PreviewSizing:
    """Keep automatic modes and manual drag geometry independent of Qt."""

    def __init__(self):
        self.mode = 'compact'
        self.manual_height = None
        self._origin_height = None
        self._origin_y = None

    def begin_drag(self, height, pointer_y):
        self.mode = 'manual'
        self.manual_height = height
        self._origin_height = height
        self._origin_y = pointer_y

    def drag_to(self, pointer_y, viewport_height, chrome_height):
        desired = self._origin_height + pointer_y - self._origin_y
        self.manual_height = min(max(60, desired), preview_limit(viewport_height, chrome_height))
        return self.manual_height

    def end_drag(self):
        self._origin_height = None
        self._origin_y = None

    def toggle(self, expanded):
        self.mode = 'expanded' if expanded else 'compact'
        self.manual_height = None
        self.end_drag()

    def fit(self, content_height, viewport_height, chrome_height):
        cap = preview_limit(viewport_height, chrome_height)
        if self.mode == 'manual':
            self.manual_height = min(max(60, self.manual_height), cap)
            return self.manual_height
        limit = 300 if self.mode == 'expanded' else 150
        return min(max(1, content_height), limit, cap)
