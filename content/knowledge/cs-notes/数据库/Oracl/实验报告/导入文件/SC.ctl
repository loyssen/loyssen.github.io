load data
infile 'D:\course\ObsidianNotes\计算机学习笔记\数据库\Oracl\实验报告\导入文件\SC.txt'
into table userfhb1.sc
(sno	position(01:01) char,
 cno	position(02:04) char,
 grade	position(07:08) integer external
)
