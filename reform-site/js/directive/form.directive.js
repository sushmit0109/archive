/* globals $ */
'use strict';

angular.module('app')
    .directive('showValidation', function($timeout) {
        return {
            restrict: 'A',
            require: 'form',
            link: function (scope, element) {
                element.find('.form-group').each(function() {
                    var $formGroup = $(this);
                    var $inputs = $formGroup.find('input[ng-model],textarea[ng-model],select[ng-model]');

                    if ($inputs.length > 0) {
                        $inputs.each(function() {
                            var $input = $(this);
                            scope.$watch(function() {
                                return $input.hasClass('ng-invalid') && $input.hasClass('ng-dirty');
                            }, function(isInvalid) {
                                $formGroup.toggleClass('has-error', isInvalid);
                            });
                        });
                    }
                });

                $timeout(
                    function() {
                        try{
                            var formInput = $('input[required], select[required], textarea[required]');
                            var formLabel = formInput.parent().parent().find('label');
                            var labelHtml = formLabel.html();
                            if (labelHtml.indexOf("*") == -1){
                                formLabel.append("<strong style='color:red'> * </strong>");
                            }
                        }catch(e) {}
                    }
                );

            }
        };
    });
