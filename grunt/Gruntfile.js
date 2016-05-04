/*global module:false*/
module.exports = function(grunt) {

  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),

    bumpup: {
      file: 'package.json'
    },

    replace: {
      dist: {
        options: {
          patterns: [
            {
              match: 'buildversion',
              replacement: '<%= pkg.version %>'
            },
            {
              match: 'deploymentregion',
              replacement: '<%= pkg.key_disabler.lambda.deployment_region %>'
            },
            {
              match: 'serviceaccount',
              replacement: '<%= pkg.key_disabler.iam.serviceaccount %>'
            },
            {
              match: 'emailreportto',
              replacement: '<%= pkg.key_disabler.email.report_to %>'
            },
            {
              match: 'emailreportfrom',
              replacement: '<%= pkg.key_disabler.email.report_from %>'
            },
            {
              match: 'emailsendcompletionreport',
              replacement: '<%= pkg.key_disabler.email.send_completion_report %>'
            },
            {
              match: 'first_warning',
              replacement: '<%= pkg.key_disabler.first_warning %>'
            },
            {
              match: 'last_warning',
              replacement: '<%= pkg.key_disabler.last_warning %>'
            },
            {
              match: 'expiry',
              replacement: '<%= pkg.key_disabler.expiry %>'
            }
          ]
        },
        files: [
          {expand: true, flatten: true, src: ['../lambda/src/RotateAccessKey.py'], dest: '../lambda/build/'}
        ]
      }
    },

    rename: {
      release: {
        files: [{
          src: ['../releases/AccessKeyRotationPackage.zip'],
          dest: '../releases/AccessKeyRotationPackage.<%= pkg.version %>.zip'
        }]
      }
    },

    exec: {
      create_lambda_policy: {
        cmd: './scripts/createLambdaAccessKeyRotationPolicy.sh "<%= pkg.key_disabler.iam.lambda.policyname %>" "<%= pkg.key_disabler.iam.lambda.rolename %>" <%= pkg.key_disabler.lambda.deployment_region %>'
      },
      package_lambda_function: {
        cmd: './scripts/createZipPackage.sh'
      },
      create_lambda_function: {
        cmd: './scripts/createLambdaFunction.sh AccessKeyRotationPackage.<%= pkg.version %>.zip <%= pkg.version %> "<%= pkg.key_disabler.lambda.function_name %>" "<%= pkg.key_disabler.iam.lambda.rolename %>" <%= pkg.key_disabler.lambda.timeout %> <%= pkg.key_disabler.lambda.memory %> <%= pkg.key_disabler.lambda.deployment_region %>'
      },
      create_scheduled_event: {
        cmd: './scripts/createScheduledEvent.sh "<%=pkg.key_disabler.lambda.function_name %>" "<%= pkg.key_disabler.lambda.schedule.rulename %>" "<%= pkg.key_disabler.lambda.schedule.description %>" "<%= pkg.key_disabler.lambda.schedule.expression %>" <%= pkg.key_disabler.aws_account_number %> <%= pkg.key_disabler.lambda.deployment_region %>'
      },
    }

  });

  // Load NPM grunt tasks
  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-exec');
  grunt.loadNpmTasks('grunt-replace');
  grunt.loadNpmTasks('grunt-contrib-rename');
  grunt.loadNpmTasks('grunt-bumpup');

  // Default task.
  //grunt.registerTask('default', 'watch');

  grunt.registerTask('build', ['replace']);
  grunt.registerTask('renamePackage', 'rename:release');

  grunt.registerTask('createLambdaPolicy', 'exec:create_lambda_policy');
  grunt.registerTask('packageLambdaFunction', 'exec:package_lambda_function');
  grunt.registerTask('createLambdaFunction', 'exec:create_lambda_function');
  grunt.registerTask('createScheduledEvent', 'exec:create_scheduled_event');

  grunt.registerTask('deployLambda', ['build', 'exec:package_lambda_function', 'renamePackage', 'exec:create_lambda_policy', 'exec:create_lambda_function', 'exec:create_scheduled_event']);
};
