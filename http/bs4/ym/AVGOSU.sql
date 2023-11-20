-- DROP TABLE IF EXISTS `AVGOSU`
CREATE TABLE `AVGOSU`
(
	`avgosu_no`				INT NOT NULL AUTO_INCREMENT COMMENT 'AVGOSU에서 수집한 정보의 고유번호'
	, `detail_url`			VARCHAR(255) NOT NULL COMMENT 'AVGOSU 상세정보 주소' COLLATE 'utf8mb4_unicode_ci'
	, `film_id`				VARCHAR(50) NOT NULL COMMENT '품번' COLLATE 'utf8mb4_unicode_ci'
	, `title`				VARCHAR(500) NOT NULL COMMENT '제목' COLLATE 'utf8mb4_unicode_ci'
	, `avgosu_date`			DATETIME NOT NULL COMMENT 'AVGOSU 기준 등록일'
	, `file_size`			VARCHAR(50) NOT NULL COMMENT '파일 용량'
	, `cover_image_url`		VARCHAR(255) NULL COMMENT '표지 이미지 주소 정보' COLLATE 'utf8mb4_unicode_ci'
	, `thumbnail_url`		VARCHAR(255) NULL COMMENT '썸네일 이미지 주소 정보' COLLATE 'utf8mb4_unicode_ci'
	, `magnet_addr`			VARCHAR(200) NULL COMMENT '마그넷 주소' COLLATE 'utf8mb4_unicode_ci'
	, `resolution`			TINYINT NOT NULL DEFAULT 0 COMMENT '화면 해상도: "F"=FHD, "H"=HD, "S"=SD, "4"=4K'
	, `reg_date`			DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP() COMMENT '정보 수집시각'

	, PRIMARY KEY (`avgosu_no`) USING BTREE
	, UNIQUE INDEX `UK_FILM_ID_FILE_SIZE` (`film_id`, `file_size`) USING BTREE
)
COMMENT='AVGOSU에서 수집한 정보 테이블'
COLLATE='utf8mb4_unicode_ci'
ENGINE=InnoDB

/*
-- URL 정보에서 호스트 정보 제거하고 경로정보만 남겨 두기
UPDATE `AVGOSU` SET
	detail_url = REPLACE(detail_url, 'https://avgosu1.com', '')
	, cover_image_url = REPLACE(cover_image_url, 'https://avgosu1.com', '')
	, thumbnail_url = REPLACE(thumbnail_url, 'https://avgosu1.com', '')
;

UPDATE `AVGOSU` SET
	resolution = 'H'
WHERE file_size LIKE '2.%'
*/