angular.module('app').controller('ChapterController', function($scope,Chapter) {

    $scope.chapters=[];
    $scope.currentPage = 0;
    $scope.numPerPage = 0;
    $scope.maxSize = 0;
    $scope.totalElement = 0;
    Chapter.get(function (data) {
        console.log(data)
        $scope.chapters = data.content;
        $scope.numPerPage = data.size;
        $scope.maxSize = 20;
        $scope.currentPage = data.currentIndex;
        $scope.totalElement = data.totalElements;

    })

}).controller('ChapterAddController', function($scope, $rootScope, $stateParams,$state, Chapter, AllBook) {
    $scope.chapters=[{book:{}}];
    $scope.object={};
    $scope.books=[];
    $scope.fieldKey=$rootScope.fieldKey;
    AllBook.get(function (data) {
        $scope.books = data;
        angular.forEach($scope.books, function(object, $index) {
            object.titleBangla = book.nameBangla+'  এর প্রতিবেদন ';
            object.title = 'Report of the '+book.name;
        });
    })
    if($stateParams.id) {
        Chapter.get({id:$stateParams.id},function (data) {
            $scope.object = data;
            $scope.chapters = [$scope.object]
        })
    }

    $scope.addMoreContent = function() {
        var serial = $scope.chapters[$scope.chapters.length-1].serial;
        console.log(serial)
        $scope.chapters.push({book:{}, serial:serial+1});
    };
    $scope.removeContent = function($index) {
        $scope.chapters.splice($index, 1);
    };
    var onSaveSuccess = function (data) {
        $scope.globalMessage = "Chapter Added Successfully";
        $state.go('chapters',null, {reload:true})
    };

    var onSaveError = function (result) {
        console.log(result);
        $state.formErrors = "Error Saving Chapter";
    };
    $scope.save = function() {
        console.log($scope.itemType)
        angular.forEach($scope.chapters, function(object, $index) {
            object.book.id = $scope.object.book.id;
        });
        Chapter.save($scope.chapters, onSaveSuccess, onSaveError);
    };
}).controller('PreviewBookController', function($scope, $rootScope, $stateParams,$state, Book, AllBook, ChapterByCommission, VolumeWiseChapterByCommission) {
    $scope.chapters = [];
    $scope.volumes = [];
    $scope.cid = null;
    $scope.sCid = null;
    $scope.vid = null;
    $scope.searchKey = "";
    $scope.showLoading = false;
    // $scope.fieldKey=$rootScope.fieldKey;
    AllBook.get(function (data) {
        $scope.books = data;
        angular.forEach($scope.books, function(object, $index) {
            object.titleBangla = object.nameBangla+'  এর প্রতিবেদন ';
            object.title = 'Report of the '+object.name;
        });
    })
    if($stateParams.id) {
        $scope.showLoading = true;
        Book.get({id:$stateParams.id},function (data) {
            $scope.book = data;
            $scope.book.titleBangla = $scope.book.nameBangla+'  এর প্রতিবেদন ';
            $scope.book.title = 'Report of the '+$scope.book.name;
            console.log( $scope.book);
            if($scope.book.hasVolume) {
                VolumeWiseChapterByCommission.get({id:$stateParams.id},function (data) {
                    $scope.volumes = data;
                    console.log( $scope.volumes);
                    $scope.showLoading = false;
                })
            } else {
                ChapterByCommission.get({id:$stateParams.id},function (data) {
                    $scope.chapters = data;
                    console.log( $scope.chapters);
                    $scope.showLoading = false;
                })
            }
        })

    }
    $scope.loadData = function() {
        $scope.showLoading = true;
        $scope.chapters = [];
        $scope.volumes = [];
        console.log($scope.book)
        if($scope.book.hasVolume) {
            VolumeWiseChapterByCommission.get({id:$scope.book.id},function (data) {
                $scope.volumes = data;
                console.log( $scope.volumes);
                $scope.showLoading = false;
            })

        } else {
            ChapterByCommission.get({id:$scope.book.id},function (data) {
                $scope.chapters = data;
                console.log( $scope.chapters);
                $scope.showLoading = false;
            })
        }
        $scope.vid = null;
        $scope.cid = null;
        $scope.sCid = null;
        // ChapterByCommission.get({id:$scope.book.id},function (data) {
        //     $scope.chapters = data;
        //     $scope.showLoading = false;
        // })
    };
    // AllChapter.get(function (data) {
    //     $scope.chapters = data;
    //     console.log($scope.chapters)
    // })
    // $scope.expandVolume = function (e, cid) {
    //     console.log("clicking on toggel");
    //     e.preventDefault();
    //     // console.log($(e.currentTarget).siblings('ul').find('li').length)
    //     $('a').removeClass('active-category')
    //     $('ul').removeClass('sub-category')
    //     if($(e.currentTarget).siblings('ul').find('li').length>0) {
    //         $(e.currentTarget).toggleClass('active-category');
    //         $(e.currentTarget).siblings('ul').toggleClass('sub-category')
    //     }
    //     $scope.cid = cid;
    //     $scope.sid = null;
    //     // console.log($(e.currentTarget).closest('ul'));
    // };
    $scope.expandVolume = function (e, vid) {
        console.log("clicking on toggel");
        e.preventDefault();
        // console.log($(e.currentTarget).siblings('ul').find('li').length)
        if(vid != $scope.vid) {
            $('a').removeClass('active-category')
            $('ul').removeClass('sub-category')
            if ($(e.currentTarget).siblings('ul').find('li').length > 0) {
                $(e.currentTarget).toggleClass('active-category');
                $(e.currentTarget).siblings('ul').toggleClass('sub-category')
            }
            $scope.vid = vid;
            $scope.cid = null;
            $scope.sid = null;
        } else {
            $scope.vid = null;
            $('a').removeClass('active-category')
            $('ul').removeClass('sub-category')
        }
        // console.log($(e.currentTarget).closest('ul'));
    };
    $scope.expandChapter = function (e, cid, vid) {
        console.log("clicking on toggel-"+cid+"--"+vid);
        if(vid) {
            if(cid != $scope.cid) {
                e.preventDefault();
                // console.log($(e.currentTarget).siblings('ul').find('li').length)
                $(e.currentTarget).siblings('a').removeClass('active-category')
                $(e.currentTarget).siblings('ul').removeClass('sub-category')
                if($(e.currentTarget).siblings('ul').find('li').length>0) {
                    $(e.currentTarget).toggleClass('active-category');
                    $(e.currentTarget).siblings('ul').toggleClass('sub-category')
                }
                $scope.vid = vid;
                $scope.cid = cid;
                $scope.sid = null;
            } else {
                $scope.cid = null;
                $(e.currentTarget).siblings('a').removeClass('active-category')
                $(e.currentTarget).siblings('ul').removeClass('sub-category')
            }
        } else {
            if(cid != $scope.cid) {
                e.preventDefault();
                // console.log($(e.currentTarget).siblings('ul').find('li').length)
                $('a').removeClass('active-category')
                $('ul').removeClass('sub-category')
                if ($(e.currentTarget).siblings('ul').find('li').length > 0) {
                    $(e.currentTarget).toggleClass('active-category');
                    $(e.currentTarget).siblings('ul').toggleClass('sub-category')
                }
                $scope.vid = vid;
                $scope.cid = cid;
                $scope.sid = null;
            } else {
                $scope.cid = null;
                $('a').removeClass('active-category')
                $('ul').removeClass('sub-category')
            }
        }

        // console.log($(e.currentTarget).closest('ul'));
    };
    $scope.expandParagraph = function (e, cid, sid, vid) {
        console.log("clicking on toggel");
        if(vid) {
            if (sid != $scope.sid) {
                e.preventDefault();
                // console.log($(e.currentTarget).siblings('ul').find('li').length)
                $(e.currentTarget).siblings('a').removeClass('active-category')
                $(e.currentTarget).siblings('ul').removeClass('sub-category')
                if ($(e.currentTarget).siblings('ul').find('li').length > 0) {
                    $(e.currentTarget).toggleClass('active-category');
                    $(e.currentTarget).siblings('ul').toggleClass('sub-category')
                }
                $scope.vid = vid;
                $scope.cid = cid;
                $scope.sid = sid;
            } else {
                $scope.sid = null;
                $(e.currentTarget).siblings('a').removeClass('active-category')
                $(e.currentTarget).siblings('ul').removeClass('sub-category')
            }
        } else {
            if (sid != $scope.sid) {
                e.preventDefault();
                // console.log($(e.currentTarget).siblings('ul').find('li').length)
                $(e.currentTarget).siblings('a').removeClass('active-category')
                $(e.currentTarget).siblings('ul').removeClass('sub-category')
                if ($(e.currentTarget).siblings('ul').find('li').length > 0) {
                    $(e.currentTarget).toggleClass('active-category');
                    $(e.currentTarget).siblings('ul').toggleClass('sub-category')
                }
                $scope.vid = vid;
                $scope.cid = cid;
                $scope.sid = sid;
            } else {
                $scope.sid = null;
                $(e.currentTarget).siblings('a').removeClass('active-category')
                $(e.currentTarget).siblings('ul').removeClass('sub-category')
            }
        }
        // console.log($(e.currentTarget).closest('ul'));
    };
    $scope.getIframeSrc = function (pdfUrl) {
        console.log({pdfUrl})
        return './pdfs/attachment/' + pdfUrl;
    };

    $scope.searchChapter = function () {
       console.log($scope.searchKey);
        ChapterByCommission.get({id:$scope.book.id, searchKey: $scope.searchKey},function (data) {
            $scope.chapters = data;
            console.log( $scope.chapters);
        })
    };
}).controller('SummaryReportController', function($scope,AllBook) {
    $scope.books=[];

    AllBook.get(function (data) {
        $scope.books = data;
    })

}).controller('GalleryController', function($scope,$sce,VideoGallery) {
    $scope.videoGallery=[];
    $scope.maxSize = 5;
    $scope.currentPage = 1;
    $scope.totalElement = 0;
    $scope.itemsPerPage = 20;

    $scope.trustSrc = function(src) {
        return $sce.trustAsResourceUrl(src+'?rel=0');
    }
    $scope.loadData = function () {
        VideoGallery.get(function (data) {
            console.log(data)
            $scope.videoGallery = data.content;
            $scope.numPerPage = data.size;
            $scope.maxSize = 20;
            $scope.currentPage = data.number + 1;
            $scope.totalElement = data.totalElements;

        })
    }
    $scope.loadData();
});

