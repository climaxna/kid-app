/**
 * 파일목록 Script
 * @Author 오늘소프트
 */

var pageContextPath;
var $searchForm, $listForm, $downloadForm;
var $fileViewer, $serviceViewer, $thumbSlider;
var videoPlayer = null;
var pdfServer = null;
var pdfUser = null;
var slideProp = {totalCnt:0, totalPage:1, currentPage:1, seqPerTotal:0, seqPerPage:0, searchGroupNm:'', searchDataTyCd:''};
var jobdirSeq;
var imageViewer = null, simpleImageViewer = null;

function getThumbList(idnbr, direction)
{
  var url = contextPath + "/data/list.json";
  var paramData = {jobdirSeq : jobdirSeq};
  if(idnbr != null) { paramData.idnbr = idnbr;}
  if(direction == 'prev') { paramData.filePageIndex = slideProp.currentPage - 1; }
  if(direction == 'next') { paramData.filePageIndex = slideProp.currentPage + 1; }
//  if(slideProp.searchGroupNm.length > 0) { paramData.searchGroupNm = slideProp.searchGroupNm; }
//  if(slideProp.searchDataTyCd.length > 0) { paramData.searchDataTyCd = slideProp.searchDataTyCd; }
  paramData.searchGroupNm = $("input[name=searchGroupNm]", $listForm).val();
  paramData.searchDataTyCd = $("input[name=searchDataTyCd]", $listForm).val();
  paramData.searchKeyword = $("input[name=searchKeyword]", $listForm).val();
  
  $.ajax({
      method : "POST"
    , url : url
    , data : paramData
    , dataType : "json"
    , cache : false
    , async : false
    , success : function(rst, textStatus, XMLHttpRequest) {
      if(rst.result) {
        slideProp = rst.info;

        var html = "", imageUrl = "";
        for(var i=0; i<rst.list.length; i++)
        {
          imageUrl = "";
          if(rst.list[i].thumbFileNm == 'noimage.png'){
            imageUrl = contextPath + "/images/archive/image.jpg";
          } else if(nvl(rst.list[i].thumbFileNm).length > 0) {
            imageUrl = contextPath + "/archiveImage/thumb.do?idnbr=" + rst.list[i].idnbr;
          } else if(rst.list[i].dataTyCd == '1') {
            imageUrl = contextPath + "/images/archive/image.jpg";
          } else if(rst.list[i].dataTyCd == '2') {
            imageUrl = contextPath + "/images/archive/video.jpg";
          } else if(rst.list[i].dataTyCd == '3') {
            imageUrl = contextPath + "/images/archive/audio.jpg";
          } else if(rst.list[i].dataTyCd == '4') {
            imageUrl = contextPath + "/images/archive/book.jpg";
          } else if(rst.list[i].dataTyCd == '5') {
            imageUrl = contextPath + "/images/archive/file.jpg";
          }
          
          html += "<div class=\"fileBox\">";
          html += "<div class=\"imageBox text-center\" data-idnbr=\""+rst.list[i].idnbr+"\"><a href=\"#\" title=\""+rst.list[i].name+"\" ><img src=\""+imageUrl+"\" alt=\""+rst.list[i].name+"\" /></a></div>";
          html += "<div class=\"fileBoxTitle\">";
          if (rst.list[i].externalData != "Y") {
	          if(nvl(rst.list[i].koglcd).length > 0 && (rst.list[i].koglcd == '1' || rst.list[i].koglcd == '2' || rst.list[i].koglcd == '3' || rst.list[i].koglcd == '4' ) ) {
	              html += "<label class=\"checkbox-wrap\">";
	        	  html += "<input type=\"checkbox\" name=\"idnbrs\" value=\""+rst.list[i].idnbr+"\" title=\""+rst.list[i].name+" 선택\" />";
	              html += "<i class=\"check-icon\"></i>";
	              html += "</label>";
	          }
          }
          html += "</div>";
          html += "</div>";
        }
        $(".thumbList", $thumbSlider).html(html);
        
        // checkbox 이벤트 핸들러 설정
        $("input[name=idnbrs]:checkbox", $thumbSlider).change(function(){
          fnCheckedIdnbr($(this).val(), $(this).prop("checked"));
        });
        
        // 체크 초기화 세팅
        $("input[name=idnbrs]", $listForm).each(function(){
          fnCheckedIdnbr($(this).val(), true);
        });
        
        
        // 아카이브 자료 클릭 이벤트 핸들러 설정
        $("div.imageBox", $thumbSlider).click(function(evt){
          evt.stopPropagation();
          evt.preventDefault();
          var idnbr = $(this).attr("data-idnbr");
          if(idnbr != null) {
            getMetaDataInfo(idnbr);
          }
        });
        
        /*
         * 이미지 로딩 후 리사이징
         */
        $("img", $thumbSlider).load(function(){
          fnAlignMiddleImage(this, $(this).parent());
        });
        
        // 자료 활성화
        if(idnbr != null) {
          $("div.imageBox[data-idnbr="+idnbr+"]", $thumbSlider).trigger("click");
        } else if (direction == 'prev') {
          $("div.imageBox:last", $thumbSlider).trigger("click");
        } else if (direction == 'next') {
          $("div.imageBox:first", $thumbSlider).trigger("click");
        }
      } else {
        alert(rst.errorMessage);
      }
    }
    , error : function( jqxhr, textStatus, error ) {
      var err = textStatus + ', ' + error;
      alert( "[오류발생] : " + err);
    }
  });
}


function fnCheckedIdnbr(idnbr, checked)
{
    if(idnbr == $serviceViewer.data("currentIdnbr")) {
        if($("#currentChecker").prop("checked") != checked) $("#currentChecker").prop("checked", checked);
    }
    $("input[name=idnbrs][value="+idnbr+"]:checkbox").each(function(){
        if($(this).prop("checked") != checked) {
            $(this).prop("checked", checked);
        }
    });
    if(checked){
        if($("input[name=idnbrs][value="+idnbr+"]", $listForm).length==0) $listForm.append("<input type='hidden' name='idnbrs' value='"+idnbr+"' />");
    } else {
        $("input[name=idnbrs][value="+idnbr+"]", $listForm).remove();
    }

    if ( $("input[name=idnbrs]", $listForm).length > 0 ) $("#btnDownload").show();
    else $("#btnDownload").hide();

    $(".downCnt").text($("input[name=idnbrs]", $listForm).length);
}


// 썸네일 슬라이드 이전 
function goPrevList()
{
  if(slideProp.currentPage > 1)
  {
    getThumbList(null, 'prev');
//    fnMoveSlide();
  }
}

// 썸네일 슬라이드 다음
function goNextList()
{
  if(slideProp.currentPage < slideProp.totalPage)
  {
    getThumbList(null, 'next');
//    fnMoveSlide(); 
  }
}

////////////썸네일 이미지 슬라이드 ////////////
function fnMoveSlide()
{
  slideProp.toMove = - ((slideProp.currentPage-1) * slideProp.slideSize);
  var tgt = $(".thumbList");
  tgt.animate({marginLeft: slideProp.toMove + "px"}, 1000);
}


// 이전 자료
function goPrev()
{
  var curIdnbr = $serviceViewer.data("currentIdnbr");
  if(curIdnbr) {
    var idx = $("div.imageBox",$thumbSlider).index($("div.imageBox[data-idnbr="+curIdnbr+"]",$thumbSlider));
    if(idx==-1) {
    } else if(slideProp.currentPage == 1 && idx==0) {
      alert("첫번째 자료입니다.");
    } else if(slideProp.currentPage > 1 && idx==0) {
      goPrevList();
    } else {
      var idnbr = $("div.imageBox:eq("+(idx-1)+")",$thumbSlider).attr("data-idnbr");
      getMetaDataInfo(idnbr);
    }
  }
}

// 다음 자료 
function goNext()
{
  var curIdnbr = $serviceViewer.data("currentIdnbr");
  if(curIdnbr) {
    var idx = $("div.imageBox",$thumbSlider).index($("div.imageBox[data-idnbr="+curIdnbr+"]",$thumbSlider));
    var lenIdnbrs = $("div.imageBox",$thumbSlider).length;
    if(idx==-1) {
    } else if(slideProp.currentPage == slideProp.totalPage && idx==lenIdnbrs-1) {
      alert("마지막 자료입니다.");
    } else if(slideProp.currentPage < slideProp.totalPage && idx==lenIdnbrs-1) {
      goNextList();
    } else {
      var idnbr = $("div.imageBox:eq("+(idx+1)+")",$thumbSlider).attr("data-idnbr");
      getMetaDataInfo(idnbr);
    }
  }
}

// idnbr기준 자료 보기
function goView(idnbr)
{
  $fileViewer.modal('show');
  if( $("div.imageBox[data-idnbr="+idnbr+"]", $thumbSlider).length==0 )
  {
    getThumbList(idnbr, null);
  }
  else
  {
    getMetaDataInfo(idnbr);
  }
}

// 자료정보 조회
function getMetaDataInfo(idnbr)
{
  // $.get(contextPath + "/cnts/weblog/fileView.do",{idnbr:idnbr});
  
  // google analysis
  // ga('send', 'pageview', 'layerFileView?idnbr='+idnbr);
  // ga('send', 'pageview', 'layerFileView');
  // 분석로그 수집(kcisa)
  try{ _bt_run_track (); }catch(e){console.log('분석로그수집['+e+']');}

  var url = contextPath + "/data/select.json";
  $.ajax({
      method : "POST"
    , url : url
    , data : { idnbr : idnbr }
    , dataType : "json"
    , cache : false
    , async : false
    , success : function(rst, textStatus, XMLHttpRequest) {
         if(rst.result) {
           var fileInfo = rst.metaDataInfo;
           
           // 첨부파일 미리보기 (2017-07-14)
           $("#idnbr").val(fileInfo.idnbr);
           $("#fileFormat").val(fileInfo.fileFmat);
           
           $("#preView").hide()
           var fileFormat = fileInfo.fileFmat.toLowerCase();
           if(fileFormat == "doc" || fileFormat == "docx" || fileFormat == "xls" || fileFormat == "xlsx" || fileFormat == "ppt" || fileFormat == "pptx" || fileFormat == "pdf" || fileFormat == "hwp" || fileFormat == "txt") {
               $("#preView").show();
           }
           // 첨부파일 미리보기 (2017-07-14)
           
           // 기본정보 , 현대사 구술영상 팝업 제목 부제로 변경 2022.11.15
           var dataNm = fileInfo.name;
           var yearTot = '';
           var dataNmD = '';
           if($("input[name=infoKindD]").val() == 'WR002'){
        	   dataNmD = '';
        	   
        	   //시대//////////////////////////////
        	   if(fileInfo.statementYears1 != "null" && fileInfo.statementYears1 != null && fileInfo.statementYears1 != ''){
        		   yearTot = fileInfo.statementYears1; 
        	   }
        	   
        	   if(yearTot == "" || yearTot == null){
        		   if(fileInfo.statementYears2 != null && fileInfo.statementYears2 != "null"){
        			   yearTot += fileInfo.statementYears2;
        		   }
        	   }else{
        		   if(fileInfo.statementYears2 != null && fileInfo.statementYears2 != ""){
        			   yearTot += ","+fileInfo.statementYears2; 
        		   }
        	   }
        	   
        	   if(yearTot == "" || yearTot == null){
        		   if(fileInfo.statementYears3 != null && fileInfo.statementYears3 != "null"){
        			   yearTot += fileInfo.statementYears3;
        		   }
        	   }else{
        		   if(fileInfo.statementYears3 != null && fileInfo.statementYears3 != ""){
        			   yearTot += ","+fileInfo.statementYears3; 
        		   }
        	   }
        	   
        	   if(yearTot == "" || yearTot == null){
        		   if(fileInfo.statementYears4 != null && fileInfo.statementYears4 != "null"){
        			   yearTot += fileInfo.statementYears4;
        		   }
        	   }else{
        		   if(fileInfo.statementYears4 != null && fileInfo.statementYears4 != ""){
        			   yearTot += ","+fileInfo.statementYears4; 
        		   }
        	   }
        	   
        	   if(yearTot == "" || yearTot == null){
        		   if(fileInfo.statementYears5 != null && fileInfo.statementYears5 != "null"){
        			   yearTot += fileInfo.statementYears5;
        		   }
        	   }else{
        		   if(fileInfo.statementYears5 != null && fileInfo.statementYears5 != ""){
        			   yearTot += ","+fileInfo.statementYears5; 
        		   }
        	   }
        	   
        	   //fileInfo.collectNm 주제있을때
        	   if(fileInfo.collectNm != "null" && fileInfo.collectNm != null){
        		   dataNmD = fileInfo.collectNm;
        	   }
        	   //dataNm 없고 yearTot 있을때
        	   
        	   if(dataNmD.trim() == ""){
        		   if(yearTot != null && yearTot != "null"){
        			   dataNmD += yearTot;
        		   }
        	   }else{
        		   if(yearTot != null && yearTot != ""){
        			   dataNmD += "/"+yearTot; 
        		   }
        	   }
        	   
        	   if(dataNmD.trim() == ""){
        		   
        		   if(fileInfo.spExplainer != null && fileInfo.spExplainer != "null"){
        			   dataNmD += fileInfo.spExplainer;
        		   }
        	   }else{
        		   if(fileInfo.spExplainer != null && fileInfo.spExplainer != ""){
        			   dataNmD += "/"+fileInfo.spExplainer;
        		   }
        	   }

        	   if(nvl(fileInfo.altvNm).length > 0) dataNm += " / " + fileInfo.altvNm;
        	   $("#fileTitleD").text(dataNmD);
        	   $("#dataNm").text(dataNm);
        	   
           }else if(nvl(fileInfo.altvNm).length > 0) dataNm += " / " + fileInfo.altvNm;
           $("#fileTitle, #dataNm").text(dataNm);
           
           // 생산정보
           /*
           $("input[name=prodOrg]", $form).val(fileInfo.prodOrg);
           $("input[name=prodMem]", $form).val(fileInfo.prodMem);
           $("select[name=ageInfo] option[value='"+nvl(fileInfo.ageInfo)+"']", $form).prop("selected",true);
           $("input[name=prodDt]", $form).val(fileInfo.prodDt);
           $("textarea[name=prodPlace]", $form).val(fileInfo.prodPlace);
           */
           
           // 자료내용
           // 주제분류추가
           var clsList = rst.clsList;
           var clsNmTxt = "";
           for(var i=0; clsList!=null && i<clsList.length; i++)
           {
             if(i > 0) clsNmTxt += ", ";
             clsNmTxt += clsList[i].bigClsNm + " / " + clsList[i].smClsNm;
           }
           $("#clsNm").text(clsNmTxt);
           
           // 자료연대/시기
           var dateAgeNmTxt = nvl(fileInfo.dateAgeNm);
           if(nvl(fileInfo.dataTime).length > 0) dateAgeNmTxt += " / " + fileInfo.dataTime;
           $("#dateAgeNm").text(dateAgeNmTxt);
           
           // 생산연대/시기
           var ageInfoNmTxt = nvl(fileInfo.ageInfoNm);
           if(nvl(fileInfo.prodDt).length > 0) ageInfoNmTxt += " / " + fileInfo.prodDt;
           $("#ageInfoNm").text(ageInfoNmTxt);
           
           // 한줄설명
           $("#lineDescText").text(nvl(fileInfo.lineDesc));
           
           // 소장처/유물번호
           var locationOriginTxt = nvl(fileInfo.locationOrigin);
           if(nvl(fileInfo.relicsNo).length > 0) locationOriginTxt += " / " + fileInfo.relicsNo;
           $("#locationOrigin").text(locationOriginTxt);
           
           // 키워드 
           var keywordList = rst.keywordList;
           var keyword = "";
           for (var i=0; i<keywordList.length; i++) {
             if (i>0) keyword += ", ";
             keyword += keywordList[i].keywordNm;
           }
           $("#keywordNm").text(keyword);
           
           
           // 관리정보
           $("#dataTyCdNm").text(fileInfo.dataTyCdNm);
           
           // 서비스
           // 저작권정보
           // $("input[name=koglcd]", $form).removeProp("checked").filter("[value='"+fileInfo.koglcd+"']").prop("checked",true);
           
           var koglMark = "";
           switch(fileInfo.koglcd) {
             case '1' : koglMark = "<span class='mark'><img src='" + contextPath + "/images/mark_open1.png' alt='제1유형 마크' /></span><span>제 1유형 : <strong>출처표시</strong> <a href='https://www.kogl.or.kr/info/licenseType1.do' target='_blank' title='새 창 열림'><img src='" + contextPath + "/images/ico_info.png' alt='공공누리 1유형 설명' /></a><br/>본 저작물은 공공누리 출처표시 조건에 따라 이용할 수 있습니다.</span>"; break;
             case '2' : koglMark = "<span class='mark'><img src='" + contextPath + "/images/mark_open2.png' alt='제2유형 마크' /></span><span>제 2유형 : <strong>출처표시+상업적 이용금지</strong> <a href='https://www.kogl.or.kr/info/licenseType2.do' target='_blank' title='새 창 열림'><img src='" + contextPath + "/images/ico_info.png' alt='공공누리 2유형 설명' /></a><br/>본 저작물은 공공누리 출처표시 조건에 따라 이용할 수 있습니다.</span>"; break;
             case '3' : koglMark = "<span class='mark'><img src='" + contextPath + "/images/mark_open3.png' alt='제3유형 마크' /></span><span>제 3유형 : <strong>출처표시+변경금지</strong> <a href='https://www.kogl.or.kr/info/licenseType3.do' target='_blank' title='새 창 열림'><img src='" + contextPath + "/images/ico_info.png' alt='공공누리 3유형 설명' /></a><br/>본 저작물은 공공누리 출처표시 조건에 따라 이용할 수 있습니다.</span>"; break;
             case '4' : koglMark = "<span class='mark'><img src='" + contextPath + "/images/mark_open4.png' alt='제4유형 마크' /></span><span>제 4유형 : <strong>출처표시+상업적 이용 금지+변경금지</strong> <a href='https://www.kogl.or.kr/info/licenseType4.do' target='_blank' title='새 창 열림'><img src='" + contextPath + "/images/ico_info.png' alt='공공누리 4유형 설명' /></a><br/>본 저작물은 공공누리 출처표시 조건에 따라 이용할 수 있습니다.</span>"; break;
           }
           
           // 공공누리유형이 없을 경우 해당 영역 삭제
          /* if(koglMark == "")	// 전시일 경우 
           {
        	 if($("#locationOrigin").length > 0)
        	 {
        	   $("#locationOrigin").attr("colspan", "3");
        	 }
        	 else	// 그 외
        	 {
        	   $("#keywordNm").attr("colspan", "5");
        	 }
        	 $("#ageInfoNm").attr("colspan", "3");
        	 $("#lineDescText").attr("colspan", "5");
        	 $("#koglMark").remove();
        	 $("#koglMarkTh").remove();
           }
           else	// 공공누리유형이 있을 경우 다시 생성
           {
        	 if($("#koglMark").length == 0)
        	 {
        	   if($("#locationOrigin").length > 0)
        	   {
        		 $("#keywordNm").attr("colspan", "1");
        	   }
        	   else
        	   {
        		 $("#keywordNm").attr("colspan", "3");
        	   }
        	   $("#metadataTr1").append("<th scope='col' colspan='2' id='koglMarkTh'>공공누리유형</th>");
        	   $("#metadataTr2").append("<td id='koglMark' class='text-center' colspan='2' rowspan='2' style='border-left:1px solid #6e6f72;'></td>");
        	   $("#ageInfoNm").attr("colspan", "1");
        	   $("#lineDescText").attr("colspan", "3");
        	 }
        	 $("#koglMark").html(koglMark);
           }*/
           if(koglMark == "")
           {        	
        	 $("#koglMark").remove();        	
           }
           else // 공공누리유형이 있을 경우 다시 생성
           {
        	   if($("#koglMark").length == 0){
        		   $(".kogl").append("<p id='koglMark'></p>");
        	   }
        	   $("#koglMark").html(koglMark);
           } 
           
           $(".subtitle").hide();
           $(".subtitleCon").html("").slideUp();
           $("#subtitleTab > a").text("▼자막열기");     
           // 동영상 자막 있는 경우 활성화
           if (fileInfo.dataTyCd == "2" && fileInfo.subtitle != "") {
        	 $(".subtitleCon").html(fileInfo.subtitle);
        	 $(".infoBox").show();
        	 $(".subtitle").show();
        	 $("#btn_depo").css("left","104px");
           }
           
           //녹취록 있을 때 배경 표시
           if ($("#deposition").length) {          	 
          	 //$(".infoBox").show();     
          	 $("#serviceViewer").css("margin-bottom","25px");
           }
           
           
           // 현재 활성화 썸네일 표시
           $("div.imageBox.active").removeClass("active");
           $("div.imageBox[data-idnbr="+idnbr+"]", $thumbSlider).addClass("active");
           
           // 뷰어의 checkbox 제어
           $("#currentCheckerBox:hidden").removeClass("hidden");
           var idnbrChecker = $("input[name=idnbrs][value="+idnbr+"]",$thumbSlider);
           if(idnbrChecker.length > 0) $("#currentChecker").prop("checked", idnbrChecker.prop("checked"));
           else $("#currentCheckerBox").addClass("hidden");
           
           // 뷰어 활성화
           fnViewServiceMedia(fileInfo);
           
           // 썸네일 목록 이동
           /*
           var thumbPage = Math.ceil(($("input[name=idnbrs]",$fileViewer).index(idnbrChecker)+1) / 10);
           if(thumbPage != slideProp.currentPage)
           {
             slideProp.currentPage = thumbPage;
             fnMoveSlide();
           }
           */
         } else {
           alert(rst.errorMessage);
         }
      }
    , error : function( jqxhr, textStatus, error ) {
        var err = textStatus + ', ' + error;
        alert( "[오류발생] : " + err);
      }
  });
}

function fnViewServiceMedia(currentMD)
{
  var idnbr = currentMD.idnbr;
  $serviceViewer.data("currentIdnbr", idnbr);
  
  
  // 이미지제거, 비디오정지, 오디오정지
  fnClearMedia();
  
  //의견 리스트가 있는지 확인해서 가져온다.
  $("#fileViewer").removeClass("fileViewer2");
  $("#fileViewer").removeClass("fileViewer3");
  $(".modal-right").html("");
  
  $.ajax({
      url : "/archive/join/selectChoiceList.do"
    , method : "post"
    , cache : false
    , async : false
    , data : {"idnbr" : idnbr}
    , dataType : "json"
    , success :function(data) {
    	//리스트가 있으면  
    	if (data.totCnt > 0) {
    		$("#fileViewer").removeClass("fileViewer2");
    		$("#fileViewer").addClass("fileViewer3");
	    	  $.each(data.opinionList, function(i, v) {
	    		  var appendHtml = "<ul><li>"
			                     + "<strong>" + v.proposerMessage + "</strong>"
			                     + "<span class=\"d\">" + v.proposalDt + "</span>"
			                     + "<span class=\"e\">" + replaceEmailEnc(v.proposerEmail) + "</span>"
			                     + "</li></ul>";
	    		  $(".modal-right").append(appendHtml);
	    	  });    	
    	  } else {
    		  //리스트가 없으면
    		  $("#fileViewer").removeClass("fileViewer3");
    		  $("#fileViewer").addClass("fileViewer2");
    	  }
    }
    , error : function(request,status,error) {
    	alert("문제가 발생하였습니다. 관리자에게 문의하세요.");
    }
  }); 
  
  switch(currentMD.dataTyCd)
  {
    case "1" : // 이미지
      fnAppendImage($serviceViewer, contextPath + "/archiveImage/service.do?idnbr=" + idnbr, idnbr);
      setEnableViewers(true, false, false);
      break;
    
    case "2" : // 영상
      $("#GMPlayerViewer").attr("title", currentMD.name + " 동영상");
      if(currentMD.streamsvr!=null && $.trim(currentMD.streamsvr).length > 0) {
        $("#GMPlayerViewer").attr("src",contextPath + "/resource/player/player.jsp?cid=" + currentMD.streamsvr);
        setEnableViewers(false, true, false);
      }else{
        $("#mediaPlayAlert").removeClass("hidden");
        fnAppendImage($serviceViewer, contextPath + "/archiveImage/thumb.do?idnbr=" + idnbr, idnbr);
        setEnableViewers(true, false, false);
      }
      break;
      
    case "3" : // 음원
      if(currentMD.streamsvr!=null && $.trim(currentMD.streamsvr).length > 0) {
        $("#GMPlayerViewer").attr("src",contextPath + "/resource/player/player.jsp?cid=" + currentMD.streamsvr);
        //오디오 뷰어
        setEnableViewers(false, false, true);
      }else{
        $("#mediaPlayAlert").removeClass("hidden");
        fnAppendImage($serviceViewer, contextPath + "/archiveImage/thumb.do?idnbr=" + idnbr, idnbr);
        setEnableViewers(true, false, false);
      }
      break;
      
    case "4" : // 도서
      fnAppendImage($serviceViewer, contextPath + "/archiveImage/thumb.do?idnbr=" + idnbr, idnbr);
      if (currentMD.streamsvr != null && currentMD.streamsvr.length > 0) {
        $("#ebookBtn").data("streamsvr", currentMD.streamsvr).removeClass("hidden");
      }
      setEnableViewers(true, false, false);
      break;
      
    default :
      fnAppendImage($serviceViewer, contextPath + "/archiveImage/thumb.do?idnbr=" + idnbr, idnbr);
      setEnableViewers(true, false, false);
      break;
  } // end switch
}

/* 이미지제거, 비디오정지, 오디오정지 */
function fnClearMedia()
{
  $serviceViewer.css('background-position-x', 'center');
  $("> img", $serviceViewer).remove();
  $("#mediaPlayAlert:visible").addClass("hidden");
  $("#GMPlayerViewer").addClass("hidden").attr("src","about:blank");
}

/* 서비스 이미지 뷰어 s */
var svcImageLock = false;
var lastSvcImage = null;
function fnAppendImage($viewer, imgUrl, idnbr)
{
  if(svcImageLock) {
    lastSvcImage = {imgUrl:imgUrl, idnbr:idnbr};
  } else {
    svcImageLock = true;
    var svcImg = new Image();
    svcImg.src = "" + imgUrl;
    svcImg.onload = function(){
      svcImageLock = false;
      if(idnbr == $serviceViewer.data("currentIdnbr")) {
//        fnAlignMiddleImage(svcImg, $viewer);
        var iInfo = fnAlignMiddleImageCalc(svcImg, $viewer);
        var $nImg = $(svcImg).css({position:'absolute', left:iInfo.left+'px', top:iInfo.top+'px', width:iInfo.width+'px', height:iInfo.height+'px'});
        $viewer.prepend($nImg).css('background-position-x', '-50px');
        imageViewer.loadImage($nImg);
      } else {
        fnAppendImage($viewer, lastSvcImage.imgUrl, lastSvcImage.idnbr);
      }
    };
    svcImg.onerror = function(){
      svcImg.src = contextPath + "/images/archive/noimage.png";
    };
  }
}

function setEnableViewers(isImageView, isVideoView, isAudioView)
{
  if(isVideoView || isAudioView) {
    $("#GMPlayerViewer").removeClass("hidden");
  }
}

function goEBook()
{
  var eBookUrl = $("#ebookBtn").data("streamsvr");
  if (nvl(eBookUrl).length > 0) {
    mbookzView2(pdfServer, eBookUrl, 1, '', pdfUser, '0');
  }
}



// 파일 상세정보 토글
function fnToggleMetaData()
{
  var $tblBox = $("#metaDataInfo .tableBox");
  if($tblBox.is(":hidden")){
    $("#metaDataInfoTab > a").text("▼ 파일정보");
    $tblBox.slideDown();
  }else{
    $("#metaDataInfoTab > a").text("▲ 파일정보");
    $tblBox.slideUp();
  }
}

// 동영상 자막 토글
function fnToggleSubtitle()
{
  var $tblBox = $("#subtitle .subtitleCon");
  if ($tblBox.is(":hidden")) {
	$("#subtitleTab > a").text("▲ 자막닫기");
	$tblBox.slideDown();
  } else {
	$("#subtitleTab > a").text("▼ 자막열기");
	$tblBox.slideUp();
  }
}

//동영상 자막 토글
function fnToggleDeposition()
{
  var $depoBox = $("#deposition .btn_wrap");
  if ($depoBox.is(":hidden")) {
	$("#btn_depo > a").addClass("open");
	$depoBox.slideDown();
  } else {
	$("#btn_depo > a").removeClass("open");
	$depoBox.slideUp();
  }
}


function fnAllChecked()
{
  $("input[name=idnbrs]:checkbox", $("#fileList")).prop("checked",true);
}

function fnAllUnChecked()
{
  $("input[name=idnbrs]:checkbox", $("#fileList")).removeProp("checked");
}

// 다운로드 실행
function fnDownload()
{
  var checkLength = $("input[name=idnbrs]", $listForm).length;
  if(checkLength == 0)
  {
    alert("하단 영상들 중 다운로드 할 자료를 선택해 주세요.");
    return;
  }
  
  var isValid = true;
  $("[required=required]:input:visible", $downloadForm).each(function(){
    if($(this).val().trim().length==0){
      alert($(this).attr("title") + "을(를) 입력해주세요.");
      $(this).focus();
      isValid = false;
      return false;
    }
  });
  
  var $checkField = $("input[name=chkNotice]", $downloadForm);
  if(isValid && !$checkField.is(":checked")){
    alert("이용 약관에 동의해 주세요.");
    $checkField.focus();
    isValid = false;
  }
  
  if(isValid){
    // idnbrs 처리 
    $("input[name=idnbrs]", $downloadForm).remove();
    var appendHtml = "";
    $("input[name=idnbrs]", $listForm).each(function(){
      appendHtml += "<input type='hidden' name='idnbrs' value='"+$(this).val()+"' />";
    });
    $downloadForm.append(appendHtml);
    $downloadForm.attr("action", contextPath + "/archive/useinfo/download.do").submit();
    $('#viewUseInfo').modal('hide');
    
    // 체크박스 클리어
    $("input[name=idnbrs]", $listForm).each(function(){
      fnCheckedIdnbr($(this).val(), false);
      $(this).remove();
    });
  }
}

// 활용정보입력창 보여주기
function fnViewUseInfo()
{
  var checkLength = $("input[name=idnbrs]", $listForm).length;
  if(checkLength == 0)
  {
    alert("하단 영상들 중 다운로드 할 자료를 선택해 주세요.");
    return;
  }

  $("#viewUseInfo").modal();
}

// 활용정보입력 : 구분 선택 처리
function fnCheckUsrType()
{
  var usrType = $("input[name=usrType]:checked", $downloadForm).val();
  if("2"==usrType)
  {
    $("div.usrType2:hidden",$downloadForm).removeClass("hidden");
  }
  else
  {
    $("div.usrType2:visible",$downloadForm).addClass("hidden");
  }
}

function goSearchGroupNm(searchGroupNm)
{
  if(searchGroupNm == null) $("input[name=searchGroupNm]",$listForm).val("");
  else $("input[name=searchGroupNm]",$listForm).val(searchGroupNm);
  goListDataTy('0');
}

function goListDataTy(searchDataTyCd)
{
  if(searchDataTyCd == '0') $("input[name=searchDataTyCd]",$listForm).val("");
  else $("input[name=searchDataTyCd]",$listForm).val(searchDataTyCd);
  $listForm.attr("action", contextPath + pageContextPath + "/folderView.do").submit();
}

function changeFilePageUnit()
{
  $("input[name=filePageUnit]", $listForm).val($("#selectFilePageUnit option:selected").val());
  $listForm.attr("action", contextPath + pageContextPath + "/folderView.do").submit();
}

function fn_egov_link_page(pageNo)
{
  if(pageNo)
  {
    $("input[name=filePageIndex]",$listForm).val(pageNo);
  }
  $listForm.attr("action", contextPath + pageContextPath + "/folderView.do").submit();
}

function goList()
{
  $searchForm.attr("action", contextPath + pageContextPath + "/mapFolderList.do").submit();
}

function goListSp(infoKind)
{	
  if (infoKind == "WR001") {  // 구술영상
	$searchForm.attr("action", "/data/09/mapFolderList.do").submit();
  } else { // 연구기획사업
	$searchForm.attr("action", "/data/09/mapFolderList.do?collectView=Y").submit();	  
  }
}

function showBtnPrevNext(showBtnPrev, showBtnNext)
{
  if(showBtnPrev) {
    $("#btnPrev:hidden").removeClass("hidden");
  } else {
    $("#btnPrev:visible").addClass("hidden");
  }
  
  if(showBtnNext) {
    $("#btnNext:hidden").removeClass("hidden");
  } else {
    $("#btnNext:visible").addClass("hidden");
  }
}


//활용정보입력창 보여주기
function fnViewSimpleViewer(imgUrl)
{
  $('#simpleViewer').modal();
  
  var $ssViewer = $('#simpleServiceViewer');
  if($ssViewer.find('img').length == 0) {
    var fImg = new Image();
    fImg.src = imgUrl;
    fImg.onload = function(){
      var iInfo = fnAlignMiddleImageCalc(fImg, $ssViewer);
      var $nImg = $(fImg).css({position:'absolute', left:iInfo.left+'px', top:iInfo.top+'px', width:iInfo.width+'px', height:iInfo.height+'px'});
      $ssViewer.append($nImg);
      simpleImageViewer.loadImage($nImg);
    }
  }
}

// 외부수집자료 시대선택
function changeFilePageOrder()
{	
  $("input[name=filePageOrder]", $listForm).val($("#selectFilePageOrder option:selected").val());
  $listForm.attr("action", contextPath + pageContextPath + "/folderView.do").submit();
}

// 상세화면 검색
function doSearch() {
  $("input[name=searchKeyword]", $listForm).val($("#inputSearchKeyword").val());
  $listForm.attr("action", contextPath + pageContextPath + "/folderView.do").submit();
}
  
function press(event) {
  if (event.keyCode==13) {
    doSearch();
  }
}

/*
$(window).load(function(){
  $("div.img-box-type").each(function(){
    var svcImg = $("img", $(this)).get(0);
    fnAlignMiddleImage(svcImg, $(this));
  });
  
  resizeThumbImage($("#jobdirThumb"));
});
*/

$(function(){
  $searchForm = $("#searchForm");
  $listForm = $("#listForm");
  $downloadForm = $("#downloadForm");
  $fileViewer = $("#fileViewer");
  $serviceViewer = $("#serviceViewer");
  $thumbSlider = $("#thumbSlider");
  
  imageViewer = new ImageViewer($serviceViewer);
  simpleImageViewer = new ImageViewer($('#simpleServiceViewer'));

  /*
  $("#jobdirThumb, div.img-box-type > img").on("load", function(){
    resizeThumbImage($(this));
  });
  */

  // 이미지 리사이즈
  $fileViewer.on("shown.bs.modal", function(e){
    $("img", $thumbSlider).each(function(){
      fnAlignMiddleImage(this, $(this).parent());
    });
  }).on("hide.bs.modal", function(e){
    fnClearMedia();
  });
  
  // 서비스 이미지 뷰어 핸들러
  $serviceViewer.mousemove(function(evt){
    if($(this).data("currentIdnbr"))
    {
      showBtnPrevNext((evt.pageX < $(this).offset().left + 70), (evt.pageX > ($(this).width() + $(this).offset().left -70)));
    }
  }).mouseleave(function(){
    showBtnPrevNext(false, false);
  });
  
  /*
  $("#btnPrev").on("focusin", function(){ $("#btnPrev:hidden").removeClass("hidden"); }).on("focusout", function(){ $("#btnPrev:visible").addClass("hidden"); });
  $("#btnNext").on("focusin", function(){ $("#btnNext:hidden").removeClass("hidden"); }).on("focusout", function(){ $("#btnNext:visible").addClass("hidden"); });
  */
  
  /*
  //오디오 뷰어
  $("#jquery_jplayer_audio").jPlayer({
    ready: function () {
    },
    swfPath: contextPath + "/resource/jplayer/",
    solution: "flash, html", // 유기적 세팅 안됨....
    supplied: "mp3, rtmpa, m4a, oga",
    wmode: "window",
    cssSelectorAncestor: "#audioViewer",
    useStateClassSkin: true,
    autoBlur: false,
    smoothPlayBar: true,
    keyEnabled: true,
    remainingDuration: true,
    toggleDuration: true
  });
  
  // 썸네일 슬라이드 정보
  slideProp = {
          slideSize:$(".fileBox").outerWidth() * 10
        , toMove : 0
        , currentPage : 1
        , totalPage : Math.ceil($(".fileBox").length / 10)
      };
  */

    // checkbox 동기화
    $("input[name=idnbrs]:checkbox").click(function(){
        fnCheckedIdnbr($(this).val(), $(this).prop("checked"));
    });
    $("#currentChecker").click(function(){
        var curIdnbr = $serviceViewer.data("currentIdnbr");
        if(curIdnbr) {
            fnCheckedIdnbr(curIdnbr, $(this).prop("checked"));
        }
    });
    // 선택 유지
    $("input[name=idnbrs]", $listForm).each(function(){
        fnCheckedIdnbr($(this).val(), true);
    });
    
    $("input[name=searchKeyword]", $searchForm).val("");
});

