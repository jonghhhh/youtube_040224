from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import googleapiclient
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp
import io
import pandas as pd
from tqdm import tqdm
import time

class YouTubeVideo:
    def __init__(self, api_key, video_id, video_save_folder):
        self.api_key = api_key
        #self.client_secrets_file = client_secrets_file
        self.video_id = video_id                       # 유튜브 url에서 '=' 이후의 id를 문자열로 입력
        self.video_save_folder = video_save_folder
        self.video_url = f"https://www.youtube.com/watch?v={video_id}"
        self.youtube = build('youtube', 'v3', developerKey=api_key)

    def get_video_info(self):
        """
        유튜브 영상 정보 수집
        결과 = [date, title, desc, thumbnail, views, likes, comments]
        """
        request = self.youtube.videos().list(
            part='snippet,statistics',
            id=self.video_id
        )
        response = request.execute()
        time.sleep(0.2)
        if response['items']:
            video = response['items'][0]
            date, title, desc = (
                video['snippet']['publishedAt'],  # 게재 일시
                video['snippet']['title'],  # 제목
                video['snippet']['description'],  # 설명
            )
            # thumbnail = 대표 이미지 url # 'standard' key가 없는 경우 처리도 아래 포함
            thumbnail_info = video['snippet']['thumbnails'].get('standard') or video['snippet']['thumbnails'].get('default')
            thumbnail = thumbnail_info.get('url') if thumbnail_info else None
            views, likes, comments = (
                video['statistics']['viewCount'],  # 조회 수
                video['statistics']['likeCount'],  # 좋아요  # 싫어요는 늘 0
                video['statistics']['commentCount'],  # 댓글 수
            )
        else:
            date, title, desc, thumbnail, views, likes, comments = None, None, None, None, None, None, None
        return [date, title, desc, thumbnail, views, likes, comments]

    def download_video(self):
        """
        유튜브 영상 다운로드
        """
        try:
            # 다운로드 옵션
            ydl_opts = {
                'format': 'worst',  # worst도 화질 무난. best, worst, best[height=720] 등으로 설정 가능
                'outtmpl': f'{self.video_save_folder}/%(id)s_%(uploader)s_%(view_count)s_%(title)s.%(ext)s',
                # 다운로드 파일명 및 경로 설정
            }
            # 유튜브 영상 다운로드
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.video_url])
        except Exception as e:
            print(f"다운로드 실패: %(id)s_%(title)s, 에러: {str(e)}")

    def get_subtitle(self):
        """
        유튜브 영상의 자막 수집
        """
        # Try to get the English transcript for the video
        try:
            trans = YouTubeTranscriptApi.get_transcript(self.video_id, languages=['ko'])
        except Exception as e:
            print(f"Error getting transcript: {e}")
        # If successful, process and print the transcript
        texts = [t['text'] for t in trans]
        result = ' '.join(texts)
        return result

    def get_comments(self, maxResults=100):  
        """
        유튜브 영상의 댓글 수집
        """
        comments = []
        try:
            # 첫 번째 페이지의 댓글 가져오기
            response = self.youtube.commentThreads().list(
                part='snippet',
                videoId=self.video_id,
                maxResults=maxResults # 최대 결과 수
            ).execute()
            for item in response.get('items', []):
                comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
                comments.append(comment)
        except Exception as e:
            print(str(e))
            comments.append('')
        return comments

if __name__ == "__main__":
    main()

