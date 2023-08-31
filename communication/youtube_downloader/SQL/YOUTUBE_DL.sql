-- YOUTUBE_DL 데이터 베이스 생성
CREATE DATABASE YOUTUBE_DL;

-- 'youtubeuser' DB 계정 생성
CREATE USER 'youtubeuser'@'%' IDENTIFIED BY '@!youtube~user';

-- 'youtubeuser' 계정에 대한 권한 부여
GRANT ALL PRIVILEGES ON YOUTUBE_DL.* TO 'youtubeuser'@'%' WITH GRANT OPTION;

-- 계정 대한 권한 새로 고침
FLUSH PRIVILEGES;
