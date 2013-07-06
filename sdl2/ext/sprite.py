"""Sprite, texture and pixel surface routines."""
import abc
from ctypes import byref, cast, POINTER, c_int
from .common import SDLError
from .compat import *
from .color import convert_to_color
from .ebs import System
from .window import Window
from .image import load_image
from .. import blendmode, surface, rect, video, pixels, render, rwops
from ..stdinc import Uint8, Uint32

__all__ = ["Sprite", "SoftwareSprite", "TextureSprite", "SpriteFactory",
           "SoftwareSpriteRenderer", "SpriteRenderer",
           "TextureSpriteRenderer", "RenderContext", "TEXTURE", "SOFTWARE"]

TEXTURE = 0
SOFTWARE = 1


class RenderContext(object):
    """SDL2-based rendering context for windows and sprites."""
    def __init__(self, target, index=-1,
                 flags=render.SDL_RENDERER_ACCELERATED):
        """Creates a new RenderContext for the given target.

        If target is a Window or SDL_Window, index and flags are passed
        to the relevant sdl.render.create_renderer() call. If target is
        a SoftwareSprite or SDL_Surface, the index and flags arguments are
        ignored.
        """
        self.renderer = None
        self.rendertaget = None
        if isinstance(target, Window):
            self.renderer = render.SDL_CreateRenderer(target.window, index,
                                                      flags)
            self.rendertarget = target.window
        elif isinstance(target, video.SDL_Window):
            self.renderer = render.SDL_CreateRenderer(target, index, flags)
            self.rendertarget = target
        elif isinstance(target, SoftwareSprite):
            self.renderer = render.SDL_CreateSoftwareRenderer(target.surface)
            self.rendertarget = target.surface
        elif isinstance(target, surface.SDL_Surface):
            self.renderer = render.SDL_CreateSoftwareRenderer(target)
            self.rendertarget = target
        else:
            raise TypeError("unsupported target type")

    def __del__(self):
        if self.renderer:
            render.SDL_DestroyRenderer(self.renderer)
        self.rendertarget = None

    @property
    def color(self):
        """The drawing color of the RenderContext."""
        r, g, b, a = Uint8(), Uint8(), Uint8(), Uint8()
        ret = render.SDL_GetRenderDrawColor(self.renderer, byref(r), byref(g),
                                            byref(b), byref(a))
        if ret == -1:
            raise SDLError()
        return convert_to_color((r.value, g.value, b.value, a.value))

    @color.setter
    def color(self, value):
        """The drawing color of the RenderContext."""
        c = convert_to_color(value)
        ret = render.SDL_SetRenderDrawColor(self.renderer, c.r, c.g, c.b, c.a)
        if ret == -1:
            raise SDLError()

    @property
    def blendmode(self):
        """The blend mode used for drawing operations (fill and line)."""
        mode = blendmode.SDL_BlendMode()
        ret = render.SDL_GetRenderDrawBlendMode(self.renderer, byref(mode))
        if ret == -1:
            raise SDLError()
        return mode

    @blendmode.setter
    def blendmode(self, value):
        """The blend mode used for drawing operations (fill and line)."""
        ret = render.SDL_SetRenderDrawBlendMode(self.renderer, value)
        if ret == -1:
            raise SDLError()

    def clear(self, color=None):
        """Clears the rendering context with the currently set or passed
        color."""
        if color is not None:
            tmp = self.color
            self.color = color
        ret = render.SDL_RenderClear(self.renderer)
        if color is not None:
            self.color = tmp
        if ret == -1:
            raise SDLError()

    def copy(self, src, srcrect=None, dstrect=None):
        """Copies (blits) the passed source to the target of the
        RenderContext,"""
        if isinstance(src, TextureSprite):
            texture = src.texture
        elif isinstance(src, render.SDL_Texture):
            texture = src
        else:
            raise TypeError("src must be a TextureSprite or SDL_Texture")
        ret = render.SDL_RenderCopy(self.renderer, texture, srcrect, dstrect)
        if ret == -1:
            raise SDLError()

    def present(self):
        """Refreshes the target of the RenderContext,"""
        render.SDL_RenderPresent(self.renderer)

    def draw_line(self, points, color=None):
        """Draws one or multiple lines on the rendering context."""
        # (x1, y1, x2, y2, ...)
        pcount = len(points)
        if (pcount % 4) != 0:
            raise ValueError("points does not contain a valid set of points")
        if pcount == 4:
            if color is not None:
                tmp = self.color
                self.color = color
            x1, y1, x2, y2 = points
            ret = render.SDL_RenderDrawLine(self.renderer, x1, y1, x2, y2)
            if color is not None:
                self.color = tmp
            if ret == -1:
                raise SDLError()
        else:
            x = 0
            off = 0
            SDL_Point = rect.SDL_Point
            ptlist = (SDL_Point * pcount / 2)()
            while x < pcount:
                ptlist[off] = SDL_Point(points[x], points[x + 1])
                x += 2
                off += 1
            if color is not None:
                tmp = self.color
                self.color = color
            ptr = cast(ptlist, POINTER(SDL_Point))
            ret = render.SDL_RenderDrawLines(self.renderer, ptr, pcount / 2)
            if color is not None:
                self.color = tmp
            if ret == -1:
                raise SDLError()

    def draw_point(self, points, color=None):
        """Draws one or multiple points on the rendering context."""
        # (x1, y1, x2, y2, ...)
        pcount = len(points)
        if (pcount % 2) != 0:
            raise ValueError("points does not contain a valid set of points")
        if pcount == 2:
            if color is not None:
                tmp = self.color
                self.color = color
            ret = render.SDL_RenderDrawPoint(self.renderer, points[0],
                                             points[1])
            if color is not None:
                self.color = tmp
            if ret == -1:
                raise SDLError()
        else:
            x = 0
            off = 0
            SDL_Point = rect.SDL_Point
            ptlist = (SDL_Point * pcount / 2)()
            while x < pcount:
                ptlist[off] = SDL_Point(points[x], points[x + 1])
                x += 2
                off += 1
            if color is not None:
                tmp = self.color
                self.color = color
            ptr = cast(ptlist, POINTER(SDL_Point))
            ret = render.SDL_RenderDrawPoints(self.renderer, ptr)
            if color is not None:
                self.color = tmp
            if ret == -1:
                raise SDLError()

    def draw_rect(self, rects, color=None):
        """Draws one or multiple rectangles on the rendering context."""
        # ((x, y, w, h), ...)
        if type(rects[0]) == int:
            # single rect
            if color is not None:
                tmp = self.color
                self.color = color
            x, y, w, h = rects
            ret = render.SDL_RenderDrawRect(self.renderer, x, y, w, h)
            if color is not None:
                self.color = tmp
            if ret == -1:
                raise SDLError()
        else:
            x = 0
            SDL_Rect = rect.SDL_Rect
            rlist = (SDL_Rect * len(rects))()
            for idx, r in enumerate(rects):
                rlist[idx] = SDL_Rect(r[0], r[1], r[2], r[3])
            if color is not None:
                tmp = self.color
                self.color = color
            ptr = cast(rlist, SDL_Rect)
            ret = render.SDL_RenderDrawRects(self.renderer, ptr)
            if color is not None:
                self.color = tmp
            if ret == -1:
                raise SDLError()

    def fill(self, rects, color=None):
        """Fills one or multiple rectangular areas on the rendering
        context."""
        SDL_Rect = rect.SDL_Rect
        # ((x, y, w, h), ...)
        if type(rects[0]) == int:
            # single rect
            if color is not None:
                tmp = self.color
                self.color = color
            x, y, w, h = rects
            ret = render.SDL_RenderFillRect(self.renderer, SDL_Rect(x, y, w, h))
            if color is not None:
                self.color = tmp
            if ret == -1:
                raise SDLError()
        else:
            x = 0
            rlist = (SDL_Rect * len(rects))()
            for idx, r in enumerate(rects):
                rlist[idx] = SDL_Rect(r[0], r[1], r[2], r[3])
            if color is not None:
                tmp = self.color
                self.color = color
            ptr = cast(rlist, SDL_Rect)
            ret = render.SDL_RenderFillRects(self.renderer, ptr)
            if color is not None:
                self.color = tmp
            if ret == -1:
                raise SDLError()


class Sprite(object):
    """A simple 2D object."""
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        """Creates a new Sprite."""
        super(Sprite, self).__init__()
        self.x = 0
        self.y = 0
        self.depth = 0

    @property
    def position(self):
        """The top-left position of the Sprite as tuple."""
        return self.x, self.y

    @position.setter
    def position(self, value):
        """The top-left position of the Sprite as tuple."""
        self.x = value[0]
        self.y = value[1]

    @property
    @abc.abstractmethod
    def size(self):
        """The size of the Sprite as tuple."""
        return

    @property
    def area(self):
        """The rectangular area occupied by the Sprite."""
        w, h = self.size
        return (self.x, self.y, self.x + w, self.y + h)


class SoftwareSprite(Sprite):
    """A simple, visible, pixel-based 2D object using software buffers."""
    def __init__(self, imgsurface, free):
        """Creates a new SoftwareSprite."""
        super(SoftwareSprite, self).__init__()
        self.free = free
        if not isinstance(imgsurface, surface.SDL_Surface):
            raise TypeError("surface must be a SDL_Surface")
        self.surface = imgsurface

    def __del__(self):
        """Releases the bound SDL_Surface, if it was created by the
        SoftwareSprite.
        """
        imgsurface = getattr(self, "surface", None)
        if self.free and imgsurface is not None:
            surface.SDL_FreeSurface(imgsurface)
        self.surface = None

    @property
    def size(self):
        """The size of the SoftwareSprite as tuple."""
        return self.surface.w, self.surface.h

    def __repr__(self):
        return "SoftwareSprite(size=%s, bpp=%d)" % \
            (self.size, self.surface.format.BitsPerPixel)


class TextureSprite(Sprite):
    """A simple, visible, texture-based 2D object, using a renderer."""
    def __init__(self, texture):
        """Creates a new TextureSprite."""
        super(TextureSprite, self).__init__()
        self.texture = texture
        flags = Uint32()
        access = c_int()
        w = c_int()
        h = c_int()
        ret = render.SDL_QueryTexture(texture, byref(flags), byref(access),
                                      byref(w), byref(h))
        if ret == -1:
            raise SDLError()
        self._size = w.value, h.value

    def __del__(self):
        """Releases the bound SDL_Texture."""
        if self.texture is not None:
            render.SDL_DestroyTexture(self.texture)
        self.texture = None

    @property
    def size(self):
        """The size of the TextureSprite as tuple."""
        return self._size

    def __repr__(self):
        flags = Uint32()
        access = c_int()
        w = c_int()
        h = c_int()
        ret = render.SDL_QueryTexture(self.texture, byref(flags),
                                      byref(access), byref(w), byref(h))
        if ret == -1:
            raise SDLError()
        static = "True"
        if access == render.SDL_TEXTUREACCESS_STREAMING:
            static = "False"
        return "TextureSprite(format=%d, static=%s, size=%s)" % \
            (flags.value, static, (w.value, h.value))


class SpriteFactory(object):
    """A factory class for creating Sprite components."""
    def __init__(self, sprite_type=TEXTURE, **kwargs):
        """Creates a new SpriteFactory.

        The SpriteFactory can create TextureSprite or SoftwareSprite
        instances, depending on the sprite_type being passed to it,
        which can be SOFTWARE or TEXTURE. The additional kwargs are used
        as default arguments for creating sprites within the factory
        methods.
        """
        if sprite_type == TEXTURE:
            if "renderer" not in kwargs:
                raise ValueError("you have to provide a renderer= argument")
        elif sprite_type != SOFTWARE:
            raise ValueError("stype must be TEXTURE or SOFTWARE")
        self._spritetype = sprite_type
        self.default_args = kwargs

    @property
    def sprite_type(self):
        """The sprite type created by the factory."""
        return self._spritetype

    def __repr__(self):
        stype = "TEXTURE"
        if self.sprite_type == SOFTWARE:
            stype = "SOFTWARE"
        return "SpriteFactory(sprite_type=%s, default_args=%s)" % \
            (stype, self.default_args)

    def create_sprite_renderer(self, *args, **kwargs):
        """Creates a new SpriteRenderer.

        For TEXTURE mode, the passed args and kwargs are ignored and the
        RenderContext or SDL_Renderer passed to the SpriteFactory is used.
        """
        if self.sprite_type == TEXTURE:
            return TextureSpriteRenderer(self.default_args["renderer"])
        else:
            return SoftwareSpriteRenderer(*args, **kwargs)

    def from_image(self, fname):
        """Creates a Sprite from the passed image file."""
        return self.from_surface(load_image(fname), True)

    def from_surface(self, tsurface, free=False):
        """Creates a Sprite from the passed SDL_Surface.

        If free is set to True, the passed surface will be freed
        automatically.
        """
        if self.sprite_type == TEXTURE:
            renderer = self.default_args["renderer"]
            texture = render.SDL_CreateTextureFromSurface(renderer.renderer,
                                                          tsurface)
            if not texture:
                raise SDLError()
            s = TextureSprite(texture.contents)
            if free:
                surface.SDL_FreeSurface(tsurface)
        elif self.sprite_type == SOFTWARE:
            s = SoftwareSprite(tsurface, free)
        return s

    def from_object(self, obj):
        """Creates a Sprite from an arbitrary object."""
        if self.sprite_type == TEXTURE:
            rw = rwops.rw_from_object(obj)
            # TODO: support arbitrary objects.
            imgsurface = surface.SDL_LoadBMP_RW(rw, True)
            if not imgsurface:
                raise SDLError()
            s = self.from_surface(imgsurface.contents, True)
        elif self.sprite_type == SOFTWARE:
            rw = rwops.rw_from_object(obj)
            imgsurface = surface.SDL_LoadBMP_RW(rw, True)
            if not imgsurface:
                raise SDLError()
            s = SoftwareSprite(imgsurface.contents, True)
        return s

    def from_color(self, color, size, bpp=32, masks=None):
        """Creates a sprite with a certain color.
        """
        color = convert_to_color(color)
        if masks:
            rmask, gmask, bmask, amask = masks
        else:
            rmask = gmask = bmask = amask = 0
        sf = surface.SDL_CreateRGBSurface(0, size[0], size[1], bpp, rmask,
                                          gmask, bmask, amask)
        if not sf:
            raise SDLError()
        sf = sf.contents
        fmt = sf.format.contents
        if fmt.Amask != 0:
            # Target has an alpha mask
            c = pixels.SDL_MapRGBA(fmt, color.r, color.g, color.b, color.a)
        else:
            c = pixels.SDL_MapRGB(fmt, color.r, color.g, color.b)
        ret = surface.SDL_FillRect(sf, None, c)
        if ret == -1:
            raise SDLError()
        return self.from_surface(sf, True)

    def create_sprite(self, **kwargs):
        """Creates an empty Sprite.

        This will invoke create_software_sprite() or
        create_texture_sprite() with the passed arguments and the set
        default arguments.
        """
        args = self.default_args.copy()
        args.update(kwargs)

        if self.sprite_type == TEXTURE:
            return self.create_texture_sprite(**args)
        else:
            return self.create_software_sprite(**args)

    def create_software_sprite(self, size, bpp=32, masks=None):
        """Creates a software sprite.

        A size tuple containing the width and height of the sprite and a
        bpp value, indicating the bits per pixel to be used, need to be
        provided.
        """
        if masks:
            rmask, gmask, bmask, amask = masks
        else:
            rmask = gmask = bmask = amask = 0
        imgsurface = surface.SDL_CreateRGBSurface(0, size[0], size[1], bpp,
                                                  rmask, gmask, bmask, amask)
        if not imgsurface:
            raise SDLError()
        return SoftwareSprite(imgsurface.contents, True)

    def create_texture_sprite(self, renderer, size,
                               pformat=pixels.SDL_PIXELFORMAT_RGBA8888,
                               static=True):
        """Creates a texture sprite.

        A size tuple containing the width and height of the sprite needs
        to be provided.

        TextureSprite objects are assumed to be static by default,
        making it impossible to access their pixel buffer in favour for
        faster copy operations. If you need to update the pixel data
        frequently, static can be set to False to allow a streaming
        access on the underlying texture pixel buffer.
        """
        if isinstance(renderer, render.SDL_Renderer):
            sdlrenderer = renderer
        elif isinstance(renderer, RenderContext):
            sdlrenderer = renderer.renderer
        else:
            raise TypeError("renderer must be a Renderer or SDL_Renderer")
        access = render.SDL_TEXTUREACCESS_STATIC
        if not static:
            access = render.SDL_TEXTUREACCESS_STREAMING
        texture = render.SDL_CreateTexture(sdlrenderer, pformat, access,
                                           size[0], size[1])
        if not texture:
            raise SDLError()
        return TextureSprite(texture.contents)


class SpriteRenderer(System):
    """A rendering system for Sprite components.

    This is a base class for rendering systems capable of drawing and
    displaying Sprite-based objects. Inheriting classes need to
    implement the rendering capability by overriding the render()
    method.
    """
    def __init__(self):
        super(SpriteRenderer, self).__init__()
        self.componenttypes = (Sprite,)
        self._sortfunc = lambda e: e.depth

    def render(self, sprites):
        """Renders the passed sprites.

        This is a no-op function and needs to be implemented by inheriting
        classes.
        """
        pass

    def process(self, world, components):
        """Draws the passed SoftSprite objects on the Window's surface."""
        self.render(sorted(components, key=self._sortfunc))

    @property
    def sortfunc(self):
        """Sort function for the component processing order.

        The default sort order is based on the depth attribute of every
        sprite. Lower depth values will cause sprites to be drawn below
        sprites with higher depth values.
        """
        return self._sortfunc

    @sortfunc.setter
    def sortfunc(self, value):
        """Sort function for the component processing order.

        The default sort order is based on the depth attribute of every
        sprite. Lower depth values will cause sprites to be drawn below
        sprites with higher depth values.
        """
        if not callable(value):
            raise TypeError("sortfunc must be callable")
        self._sortfunc = value


class SoftwareSpriteRenderer(SpriteRenderer):
    """A rendering system for SoftwareSprite components.

    The SoftwareSpriteRenderer class uses a Window as drawing device to
    display Sprite surfaces. It uses the Window's internal SDL surface as
    drawing context, so that GL operations, such as texture handling or
    using SDL renderers is not possible.
    """
    def __init__(self, window):
        """Creates a new SoftSpriteRenderer for a specific Window."""
        super(SoftwareSpriteRenderer, self).__init__()
        if isinstance(window, Window):
            self.window = window.window
        elif isinstance(window, video.SDL_Window):
            self.window = window
        else:
            raise TypeError("unsupported window type")
        surface = video.SDL_GetWindowSurface(self.window)
        if not surface:
            raise SDLError()
        self.surface = surface.contents
        self.componenttypes = (SoftwareSprite,)

    def render(self, sprites, x=None, y=None):
        """Draws the passed sprites (or sprite) on the Window's surface.

        x and y are optional arguments that can be used as relative
        drawing location for sprites. If set to None, the location
        information of the sprites are used. If set and sprites is an
        iterable, such as a list of SoftwareSprite objects, x and y are
        relative location values that will be added to each individual sprite's
        position. If sprites is a single SoftwareSprite, x and y denote the
        absolute position of the SoftwareSprite, if set.
        """
        r = rect.SDL_Rect(0, 0, 0, 0)
        if isiterable(sprites):
            blit_surface = surface.SDL_BlitSurface
            imgsurface = self.surface
            x = x or 0
            y = y or 0
            for sp in sprites:
                r.x = x + sp.x
                r.y = y + sp.y
                blit_surface(sp.surface, None, imgsurface, r)
        else:
            r.x = x or sprites.x
            r.y = y or sprites.y
            surface.SDL_BlitSurface(sprites.surface, None, self.surface, r)
        video.SDL_UpdateWindowSurface(self.window)


class TextureSpriteRenderer(SpriteRenderer):
    """A rendering system for TextureSprite components.

    The TextureSpriteRenderer class uses a SDL_Renderer as drawing
    device to display TextureSprite objects.
    """
    def __init__(self, target):
        """Creates a new TextureSpriteRenderer.

        target can be a Window, SDL_Window, RenderContext or SDL_Renderer.
        If it is a Window or SDL_Window instance, a RenderContext will be
        created to acquire the SDL_Renderer.
        """
        super(TextureSpriteRenderer, self).__init__()
        if isinstance(target, (Window, video.SDL_Window)):
            # Create a Renderer for the window and use that one.
            target = RenderContext(target)

        if isinstance(target, RenderContext):
            self._renderer = target  # Used to prevent GC
            sdlrenderer = target.renderer
        elif isinstance(target, render.SDL_Renderer):
            sdlrenderer = target
        else:
            raise TypeError("unsupported object type")
        self.sdlrenderer = sdlrenderer
        self.componenttypes = (TextureSprite,)

    def render(self, sprites, x=None, y=None):
        """Draws the passed sprites (or sprite).

        x and y are optional arguments that can be used as relative
        drawing location for sprites. If set to None, the location
        information of the sprites are used. If set and sprites is an
        iterable, such as a list of TextureSprite objects, x and y are
        relative location values that will be added to each individual
        sprite's position. If sprites is a single TextureSprite, x and y
        denote the absolute position of the TextureSprite, if set.
        """
        r = rect.SDL_Rect(0, 0, 0, 0)
        if isiterable(sprites):
            rcopy = render.SDL_RenderCopy
            renderer = self.sdlrenderer
            x = x or 0
            y = y or 0
            for sp in sprites:
                r.x = x + sp.x
                r.y = y + sp.y
                r.w, r.h = sp.size
                if rcopy(renderer, sp.texture, None, r) == -1:
                    raise SDLError()
        else:
            if x is None or y is None:
                r.x = sprites.x
                r.y = sprites.y
                r.w, r.h = sprites.size
            render.SDL_RenderCopy(self.sdlrenderer, sprites.texture, None, r)
        render.SDL_RenderPresent(self.sdlrenderer)
