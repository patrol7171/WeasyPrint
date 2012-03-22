# coding: utf8
"""
    weasyprint.layout.preferred
    ---------------------------

    Preferred and minimum preferred width, aka. the shrink-to-fit algorithm.

    :copyright: Copyright 2011-2012 Simon Sapin and contributors, see AUTHORS.
    :license: BSD, see LICENSE for details.

"""

from __future__ import division, unicode_literals

import cairo

from ..formatting_structure import boxes
from ..text import TextFragment
from .inlines import replaced_box_width
from .percentages import resolve_percentages


def shrink_to_fit(box, maximum_width=None):
    """Return ``(preferred_width, preferred_mimimum_width)`` for ``box``.

    If ``maximum_width`` is not ``None``, the preferred width is calculated to
    be smaller than this width.

    """
    return preferred_width(box, maximum_width), preferred_mimimum_width(box)


def preferred_mimimum_width(box):
    """Return the preferred minimum width for ``box``.

    This is the width by breaking at every line-break opportunity.

    """
    if isinstance(box, boxes.BlockContainerBox):
        return block_preferred_minimum_width(box)
    elif isinstance(box, (boxes.InlineBox, boxes.LineBox)):
        return inline_preferred_minimum_width(box)
    else:
        raise TypeError(
            'Preferred minimum width for %s not handled yet' %
            type(box).__name__)


def preferred_width(box, maximum_width=None):
    """Return the preferred width for ``box``.

    This is the width by only breaking at forced line breaks.

    If ``maximum_width`` is not ``None``, the preferred width is calculated to
    be smaller than this width.

    """
    if isinstance(box, boxes.BlockContainerBox):
        return block_preferred_width(box, maximum_width)
    elif isinstance(box, (boxes.InlineBox, boxes.LineBox)):
        return inline_preferred_width(box, maximum_width)
    else:
        raise TypeError(
            'Preferred width for %s not handled yet' % type(box).__name__)


def block_preferred_minimum_width(box):
    """Return the preferred minimum width for a ``BlockBox``."""
    if box.width == 'auto':
        if box.children:
            return max(
                preferred_mimimum_width(child) for child in box.children)
        else:
            return 0
    else:
        # TODO: handle fixed and % widths
        raise TypeError('Width %s is unknown' % box.width)


def block_preferred_width(box, maximum_width=None):
    """Return the preferred width for a ``BlockBox``."""
    if box.width == 'auto':
        if box.children:
            return max(
                preferred_width(child, maximum_width)
                for child in box.children)
        else:
            return 0
    else:
        # TODO: handle fixed and % widths
        raise TypeError('Width %s is unknown' % box.width)


def inline_preferred_minimum_width(box):
    """Return the preferred minimum width for an ``InlineBox``.

    *Warning:* only TextBox and InlineReplacedBox children are supported
    for now. (No recursive InlineBox childdren.)

    """
    widest_line = 0
    for child in box.children:
        if isinstance(child, boxes.AtomicInlineLevelBox):
            # Images are on their own line
            current_line = replaced_preferred_width(child)
        else:
            assert isinstance(child, boxes.TextBox)
            current_line = max(text_lines_width(child, width=0))
        widest_line = max(widest_line, current_line)
    return widest_line


def inline_preferred_width(box, maximum_width=None):
    """Return the preferred width for an ``InlineBox``.

    *Warning:* only TextBox and InlineReplacedBox children are supported
    for now. (No recursive InlineBox children.)

    """
    widest_line = 0
    current_line = 0
    for child in box.children:
        if isinstance(child, boxes.InlineReplacedBox):
            # No line break around images
            current_line += replaced_preferred_width(child)
        else:
            assert isinstance(child, boxes.TextBox)
            lines = list(text_lines_width(child, width=maximum_width))
            assert lines
            # The first text line goes on the current line
            current_line += lines[0]
            if len(lines) > 1:
                # Forced line break
                widest_line = max(widest_line, current_line)
                if len(lines) > 2:
                    widest_line = max(widest_line, max(lines[1:-1]))
                current_line = lines[-1]
    widest_line = max(widest_line, current_line)
    return widest_line


def text_lines_width(box, width):
    """Return the list of line widths for a ``TextBox``."""
    # TODO: find the real surface, to have correct hinting
    context = cairo.Context(cairo.PDFSurface(None, 1, 1))
    fragment = TextFragment(box.text, box.style, context, width=width)
    return fragment.line_widths()


def replaced_preferred_width(box):
    """Return the preferred (minimum) width for an ``InlineReplacedBox``."""
    # TODO: get the actual device size. Or do we really care?
    # TODO: what about percentage widths?
    resolve_percentages(box, containing_block=(0, 0))
    replaced_box_width(box, device_size=None)
    return box.width
