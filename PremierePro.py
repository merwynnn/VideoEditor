import xml.etree.ElementTree as ET


class Project:
    def __init__(self, project_path, project_name, fps, length):
        self.project_path = project_path
        self.project_name = project_name
        self.fps = fps
        self.length = length

        self.root = None
        self.project = None
        self.sequence = None
        self.media = None

        self.video_track = None
        self.audio_track = None

        self.create_premiere_pro_project()

    def create_premiere_pro_project(self):
        # Create the root element for the XML document
        self.root = ET.Element('xmeml', attrib={'version': '4'})

        # Create the project element
        self.project = ET.SubElement(self.root, 'project')

        # Set project attributes
        self.project.attrib['name'] = self.project_name

        # Create the sequence element
        self.sequence = ET.SubElement(self.project, 'sequence')

        # Set sequence attributes
        self.sequence.attrib['id'] = 'sequence-1'
        self.sequence.attrib['dur'] = str(self.length / self.fps) + '/30000s'
        self.sequence.attrib['tcFormat'] = 'DF'
        self.sequence.attrib['frameRate'] = str(self.fps) + 'p'

        # Create the media element
        self.media = ET.SubElement(self.sequence, 'media')

        # Add video and audio tracks to the media element
        self.video_track = ET.SubElement(self.media, 'video')
        self.audio_track = ET.SubElement(self.media, 'audio')

    def add_video_clip(self, clip_path, clip_name, start_frame, end_frame, offset_frame):
        clipitem = ET.SubElement(self.video_track, 'clipitem')
        file_element = ET.SubElement(clipitem, 'file')
        pathurl = ET.SubElement(file_element, 'pathurl')
        pathurl.text = clip_path
        name_element = ET.SubElement(file_element, 'name')
        name_element.text = clip_name
        in_point = ET.SubElement(clipitem, 'in')
        in_point.attrib['value'] = str(start_frame)
        out_point = ET.SubElement(clipitem, 'out')
        out_point.attrib['value'] = str(end_frame)
        start = ET.SubElement(clipitem, 'start')
        start.attrib['value'] = str(offset_frame)

    def add_audio_clip(self, clip_path, clip_name):
        clipitem = ET.SubElement(self.audio_track, 'clipitem')
        file_element = ET.SubElement(clipitem, 'file')
        name_element = ET.SubElement(file_element, 'name')
        name_element.text = clip_name
        pathurl = ET.SubElement(file_element, 'pathurl')
        pathurl.text = clip_path

    def save(self):
        # Write the XML document to the project file
        tree = ET.ElementTree(self.root)
        tree.write(self.project_path, encoding='UTF-8', xml_declaration=True)
