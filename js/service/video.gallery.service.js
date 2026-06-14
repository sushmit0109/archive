'use strict';

angular.module('app')
    .factory('VideoGallery', function () {
        return {
            get: function (callback) {
                if (callback) callback({ content: [], totalElements: 0, size: 10, number: 0 });
            }
        };
    });
