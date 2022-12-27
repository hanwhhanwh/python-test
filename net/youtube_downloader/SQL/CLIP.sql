-- DROP TABLE IF EXISTS `CLIP`
CREATE TABLE `CLIP`
(
	`clip_no`				INT NOT NULL AUTO_INCREMENT COMMENT '유튜브 고유번호'
	, `member_no`			INT NOT NULL COMMENT '작성자 고유번호 (FK: MEMBER.member_no)'
	, `clip_id`				VARCHAR(50) NOT NULL COMMENT '클립의 ID' COLLATE 'utf8mb4_general_ci'
	, `channel_id`			VARCHAR(50) NOT NULL COMMENT '채널의 ID' COLLATE 'utf8mb4_general_ci'
	, `author`				VARCHAR(255) NULL COMMENT '등록자' COLLATE 'utf8mb4_general_ci'
	, `title`				VARCHAR(1000) NULL COMMENT '클립의 제목' COLLATE 'utf8mb4_general_ci'
	, `length`				INT NULL COMMENT '시간 (초)'
	, `publish_date`		DATE NULL COMMENT '클립 등록일'
	, `thumbnail_url`		VARCHAR(1000) NULL COMMENT '썸네일 이미지 주소 정보' COLLATE 'utf8mb4_general_ci'
	, `description`			MEDIUMTEXT NULL COMMENT '클립 상세 설명' COLLATE 'utf8mb4_general_ci'
	, `reg_date`			DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP() COMMENT '클립 정보 등록시각'

	, PRIMARY KEY (`clip_no`) USING BTREE
	, UNIQUE INDEX `UK_CLIP_ID` (`clip_id`) USING BTREE
)
COMMENT='작품 기본 정보 테이블'
COLLATE='utf8mb4_general_ci'
ENGINE=InnoDB
;
