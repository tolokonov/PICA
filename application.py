import os
import random

import streamlit as st
import cv2
import tempfile
from PIL import Image, ImageFile
import numpy as np
from streamlit_option_menu import option_menu
from algorithms.image_enhancer import ImageEnhancer
from algorithms.style_transfer import StyleTransfer

ImageFile.LOAD_TRUNCATED_IMAGES = True


@st.experimental_singleton
def get_style_transfer() -> StyleTransfer:
    """"""
    return StyleTransfer()


class Application:
    def __init__(self, source_img=None, style_img=None, source_video = None):
        self.source_img = source_img
        self.style_img = style_img
        self.source_video = source_video

    def set_config(self) -> None:
        """Configurate web-site settings."""
        st.set_page_config(page_title='PICA',
                           page_icon=Image.open('assets/Pica_logo_plus.jpg'),
                           layout="centered")
        st.title('PICA')
        st.write('<style>div.block-container{padding-top:2rem;}</style>', unsafe_allow_html=True)
        st.markdown("<style>#MainMenu {visibility: hidden;}footer {visibility: hidden;}</style> ",
                    unsafe_allow_html=True)

    def run(self) -> None:
        """Run application."""
        self.create_folder()
        self.navigation()

    def navigation(self) -> None:
        """Set navigation bar"""
        with st.sidebar:
            option = option_menu(menu_title='',
                                 options=['Image', 'Video', 'Gallery', 'Reference'],
                                 icons=['image', 'camera-video', 'archive', 'link'],
                                 orientation='vertical')
        if option == 'Image':
            self.image_upload()
            self.generate()
            self.history()
        elif option == 'Video':
            self.video_image_upload()
            self.video_process()
            self.video_history()
        elif option == 'Gallery':
            st.image('assets/examples.png')
        else:
            st.markdown('You can find the network in this [paper](https://arxiv.org/abs/1705.06830).')

    def video_image_upload(self) -> None:
        """Displays two button for content and style image uploading."""
        col1, col2 = st.columns(2)
        with col1:
            src_video = st.file_uploader(label='Source video', type=['mp4', 'mov', 'avi'])
            if src_video:
                temp_file = tempfile.NamedTemporaryFile(delete=False)
                temp_file.write(src_video.read())

                temp_video = open(temp_file.name, "rb")
                video_bytes = temp_video.read()
                st.video(video_bytes)

                self.source_video = cv2.VideoCapture(temp_file.name)

        with col2:
            style_image = st.file_uploader(label='Style image', type=['png', 'jpg', 'webp'])
            if style_image:
                self.style_img = Image.open(style_image)
                st.image(style_image, caption='Style image')

    def video_process(self):
        scale = self.slider()
        if 'generate_button_status' not in st.session_state:
            st.session_state.generate_button_status = False
        try:
            placeholder = st.empty()
            generate_button = placeholder.button('Generate', disabled=False, key='1')
            if generate_button and self.source_video and self.style_img:
                placeholder.button('Generate', disabled=True, key='2')
                st.session_state.generate_button_status = True
                stframe = st.empty()

                width = int(self.source_video.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(self.source_video.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = int(self.source_video.get(cv2.CAP_PROP_FPS))

                codec = cv2.VideoWriter_fourcc(*"FMP4")
                stylized_video_number = len(os.listdir(f'generated_video')) if os.path.isdir(
                    f'generated_video') else 0
                path = f'generated_video/{stylized_video_number}.mp4'
                out = cv2.VideoWriter(path, codec, fps, (width, height))

                while self.source_video.isOpened():
                    ret, frame = self.source_video.read()
                    # if frame is read correctly ret is True
                    if not ret:
                        print("Can't receive frame (stream end?). Exiting ...")
                        break
                    frame.flags.writeable = True
                    self.source_img = cv2.blur(frame, (10, 10))
                    stylized_image = get_style_transfer().transfer_style(self.source_img, self.style_img, scale / 100 * (1080 - 360) + 360)
                    stylized_image = ImageEnhancer.reproduce_shape(stylized_image, (width, height))
                    stframe.image(stylized_image)
                    out.write(np.array(stylized_image))

                out.release()
                self.source_video.release()
                placeholder.button('Generate', disabled=False, key='3')
                placeholder.empty()
                st.experimental_rerun()
        except Exception as e:
            st.error('Something went wrong...')
            st.error('We are already working to fix this bug!')
            st.write(e)

    def video_history(self):
        path = f'generated_video'
        if len(os.listdir(path)) > 0 and st.button('Clean history'):
            for video in os.listdir(path):
                os.remove(f'{path}/{video}')

        if len(os.listdir(path)) > 0:
            cols_in_grid = 5
            cols = st.columns(cols_in_grid)
            for index, video in enumerate(os.listdir(path)):
                with cols[index % cols_in_grid]:
                    st.write(video)
                    with open(f'{path}/{video}', 'rb') as file:
                        with st.container():
                            st.download_button(label='Download',
                                               data=file,
                                               file_name=f'stylized_{video}',
                                               mime='video/mp4',
                                               key=random.randint(0, 10000))
                    if st.button(label='Delete', key=f'delete-button-{video}'):
                        os.remove(f'{path}/{video}')
                        st.experimental_rerun()

    def image_upload(self) -> None:
        """Displays two button for content and style image uploading."""
        col1, col2 = st.columns(2)
        with col1:
            src_image = st.file_uploader(label='Source image', type=['png', 'jpg', 'webp'])
            if src_image:
                self.source_img = Image.open(src_image)
                st.image(src_image, caption='Source image')

        with col2:
            style_image = st.file_uploader(label='Style image', type=['png', 'jpg', 'webp'])
            if style_image:
                self.style_img = Image.open(style_image)
                st.image(style_image, caption='Style image')

    def create_folder(self) -> None:
        """Create folders if they do not exist"""
        if not os.path.isdir('generated_images/'):
            os.mkdir('generated_images/')

    def generate(self) -> None:
        """Generates stylized image on button click and ave to history."""
        scale = self.slider()
        if 'generate_button_status' not in st.session_state:
            st.session_state.generate_button_status = False
        try:
            placeholder = st.empty()
            generate_button = placeholder.button('Generate', disabled=False, key='1')
            if generate_button and self.source_img and self.style_img:
                placeholder.button('Generate', disabled=True, key='2')
                st.session_state.generate_button_status = True
                stylized_image = get_style_transfer().transfer_style(self.source_img, self.style_img,
                                                                     scale / 100 * (1080 - 360) + 360)
                stylized_image = ImageEnhancer.reproduce_shape(stylized_image, self.source_img.size)
                stylized_image = ImageEnhancer.increase_saturation(stylized_image, 1.15)
                stylized_image_number = len(os.listdir(f'generated_images')) if os.path.isdir(
                    f'generated_images') else 0
                stylized_image.save(f'generated_images/{stylized_image_number}.png')
                placeholder.button('Generate', disabled=False, key='3')
                placeholder.empty()
                st.experimental_rerun()
        except Exception as e:
            st.error('Something went wrong...')
            st.error('We are already working to fix this bug!')
            st.write(e)

    def slider(self) -> int:
        """Display slider.
        Returns:
            intensity value (int)"""
        return st.slider(label='Intensity', min_value=0, max_value=100, value=50, step=1)

    def history(self):
        """Displays history of generated images"""
        path = f'generated_images'
        if len(os.listdir(path)) > 0 and st.button('Clean history'):
            for image in os.listdir(path):
                os.remove(f'{path}/{image}')

        if len(os.listdir(path)) > 0:
            stylized_images = [Image.open(path + '/' + image) for image in os.listdir(path)][::-1]
            cols_in_grid = 5
            cols = st.columns(cols_in_grid)
            for index, image in enumerate(stylized_images):
                with cols[index % cols_in_grid]:
                    st.image(stylized_images[index], caption='Stylized image', use_column_width='always')
                    with open(image.filename, 'rb') as file:
                        with st.container():
                            st.download_button(label='Download',
                                               data=file,
                                               file_name=f'stylized_{image.filename}',
                                               mime='image/png',
                                               key=random.randint(0, 10000))
                    if st.button(label='Delete', key=f'delete-button-{image.filename}'):
                        os.remove(f'{image.filename}')
                        st.experimental_rerun()
