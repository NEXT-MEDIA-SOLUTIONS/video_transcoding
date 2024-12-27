## Install or update the AWS CLI

https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html

at date u can just use for windows env in a CMD: 

msiexec.exe /i https://awscli.amazonaws.com/AWSCLIV2.msi






docker build -t video-transcoding .
docker run -d -p 9000:8080 --name mh video-transcoding


aws ecr get-login-password --region eu-west-1 | docker login --username AWS --password-stdin 893201506378.dkr.ecr.eu-west-1.amazonaws.com

aws lambda update-function-configuration --function-name video_transcoding --package-type Image

aws lambda update-function-code --function-name video_transcoding --image-uri 893201506378.dkr.ecr.eu-west-1.amazonaws.com/video-transcoding:latest
aws lambda update-function-configuration --function-name video_transcoding --image-config '{"EntryPoint": ["python", "app.py"], "Command": [], "WorkingDirectory": "/var/task"}'


```sql
CREATE DATABASE provisioning;
CREATE EXTERNAL TABLE provisioning.btvs_ids( content_id string, pub_id string, add_at timestamp)
PARTITIONED BY (id int)
ROW FORMAT SERDE 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe'
STORED AS INPUTFORMAT 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat'
OUTPUTFORMAT 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION 's3://rmcbfmads-creatives/provisioning/btvs_ids'
TBLPROPERTIES ( 'parquet.enable.dictionary'='true')
;
commit;

show create table test_data.btvs_ids;

INSERT INTO provisioning.btvs_ids (id, content_id, pub_id, add_at)
        VALUES (10, null, null, current_timestamp);
        
select * from provisioning.btvs_ids;
```


```xml
<transcode>
    <sessionId>38-1</sessionId>
    <creative>
        <name>TestAd_5s_A</name>
        <networkId>88881</networkId>
        <sourceCreativeRendition>
            <id>FR_ORSG_SHIE_SHIN_0005_020_F</id>
            <location>https://s1.fwmrm.net/m/1/515295/19/145138835/578112393/240327_SHINE_TOILETTEUSE_20SEC_ADSTREAM_1_1712326321.mp4</location>
        </sourceCreativeRendition>
        <creativeRendition>
            <contentType>xxxxxx</contentType>
            <id3>
                <key>TIT2</key>
                <value>fw_888811201</value>
            </id3>
        </creativeRendition>
    </creative>
</transcode>


<transcode>
    <sessionId>38-1</sessionId>
    <creative>
        <name>TestAd_5s_A</name>
        <networkId>88881</networkId>
        <sourceCreativeRendition>
            <id>FR_ORSG_SHIE_SHIN_0006_020_F</id>
            <location>https://s1.fwmrm.net/m/1/515295/36/145138724/578111787/240327_SHINE_ARCHI_20SEC_ADSTREAM_1712326250.mp4</location>
        </sourceCreativeRendition>
        <creativeRendition>
            <contentType>xxxxxx</contentType>
            <id3>
                <key>TIT2</key>
                <value>fw_888811201</value>
            </id3>
        </creativeRendition>
    </creative>
</transcode>




<transcode>
    <sessionId>38-1</sessionId>
    <creative>
        <name>TestAd_5s_A</name>
        <networkId>88881</networkId>
        <sourceCreativeRendition>
            <id>FR_ERAC_TCLL_RENT_0023_020_F</id>
            <location>https://s1.fwmrm.net/m/1/515295/92/148352860/593124885/FR_ERAC_TCLL_RENT_0023_020_F__1713949032.mp4</location>
        </sourceCreativeRendition>
        <creativeRendition>
            <contentType>xxxxxx</contentType>
            <id3>
                <key>TIT2</key>
                <value>fw_888811201</value>
            </id3>
        </creativeRendition>
    </creative>
</transcode>






FR_ERAC_TCLL_RENT_0021_020_F:   https://s1.fwmrm.net/m/1/515295/27/148352795/593124431/FR_ERAC_TCLL_RENT_0021_020_F_1713948929.mp4
FR_ERAC_TCLL_RENT_0022_020_F:   https://s1.fwmrm.net/m/1/515295/66/148352834/593124700/FR_ERAC_TCLL_RENT_0022_020_F_1713948974.mp4
FR_ERAC_TCLL_RENT_0023_020_F:   https://s1.fwmrm.net/m/1/515295/92/148352860/593124885/FR_ERAC_TCLL_RENT_0023_020_F__1713949032.mp4

<transcode>
    <sessionId>38-1</sessionId>
    <creative>
        <name>TestAd_5s_A</name>
        <networkId>88881</networkId>
        <sourceCreativeRendition>
            <id>FR_ERAC_TCLL_RENT_0021_020_F</id>
            <location>https://s1.fwmrm.net/m/1/515295/27/148352795/593124431/FR_ERAC_TCLL_RENT_0021_020_F_1713948929.mp4</location>
        </sourceCreativeRendition>
        <creativeRendition>
            <contentType>xxxxxx</contentType>
            <id3>
                <key>TIT2</key>
                <value>fw_888811201</value>
            </id3>
        </creativeRendition>
    </creative>
</transcode>


<transcode>
    <sessionId>38-1</sessionId>
    <creative>
        <name>TestAd_5s_A</name>
        <networkId>88881</networkId>
        <sourceCreativeRendition>
            <id>FR_ERAC_TCLL_RENT_0022_020_F</id>
            <location>https://s1.fwmrm.net/m/1/515295/66/148352834/593124700/FR_ERAC_TCLL_RENT_0022_020_F_1713948974.mp4</location>
        </sourceCreativeRendition>
        <creativeRendition>
            <contentType>xxxxxx</contentType>
            <id3>
                <key>TIT2</key>
                <value>fw_888811201</value>
            </id3>
        </creativeRendition>
    </creative>
</transcode>



<transcode>
    <sessionId>38-1</sessionId>
    <creative>
        <name>TestAd_5s_A</name>
        <networkId>88881</networkId>
        <sourceCreativeRendition>
            <id>FR_BETC_GLEC_LECL_0391_030_F</id>
            <location>https://s1.fwmrm.net/m/1/515295/0/163308544/646553545/pubid_FR_BETC_GLEC_LECL_0391_030_F_1720424385_1720433553.mp4</location>
        </sourceCreativeRendition>
        <creativeRendition>
            <contentType>xxxxxx</contentType>
            <id3>
                <key>TIT2</key>
                <value>fw_888811201</value>
            </id3>
        </creativeRendition>
    </creative>
</transcode>


<transcode>
    <sessionId>38-1</sessionId>
    <creative>
        <name>TestAd_5s_A</name>
        <networkId>88881</networkId>
        <sourceCreativeRendition>
            <id>FR_THPS_ESFRTENA_0064_020_F</id>
            <location>https://s1.fwmrm.net/m/1/515295/24/163470360/647290795/pubid_FR_THPS_ESFRTENA_0064_020_F_1720451318_1720532587.mp4</location>
        </sourceCreativeRendition>
        <creativeRendition>
            <contentType>xxxxxx</contentType>
            <id3>
                <key>TIT2</key>
                <value>fw_888811201</value>
            </id3>
        </creativeRendition>
    </creative>
</transcode>

```