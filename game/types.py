from utils.types import PlayerId

type FilePath = str
"a to a local file"
type ImagePath = FilePath
"a to a local image"
type ImagePathWithCaption = tuple[ImagePath,str]
"a tuple of a path to an image and a caption"
type PlayerMessage = tuple[PlayerId,str|None]
"a tuple of the player and the content of their message"