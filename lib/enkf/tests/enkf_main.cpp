/*
   Copyright (C) 2013  Equinor ASA, Norway.

   The file 'enkf_main.c' is part of ERT - Ensemble based Reservoir Tool.

   ERT is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   ERT is distributed in the hope that it will be useful, but WITHOUT ANY
   WARRANTY; without even the implied warranty of MERCHANTABILITY or
   FITNESS FOR A PARTICULAR PURPOSE.

   See the GNU General Public License at <http://www.gnu.org/licenses/gpl.html>
   for more details.
*/
#include <stdlib.h>
#include <stdbool.h>
#include <stdio.h>
#include <unistd.h>

#include <ert/util/test_util.h>
#include <ert/util/test_work_area.h>
#include <ert/util/util.h>

#include <ert/enkf/enkf_main.hpp>
#include <ert/enkf/model_config.hpp>




void test_case_initialized(const char * config_path, const char * config_file) {
  test_work_area_type * work_area = test_work_area_alloc("enkf_main_case_initialized");
  test_work_area_copy_directory_content(work_area, config_path);
  {
    res_config_type * res_config = res_config_alloc_load(config_file);
    enkf_main_type * enkf_main = enkf_main_alloc(res_config, true, true);
    model_config_type * model_config = enkf_main_get_model_config(enkf_main);
    const char * new_case = "fs/case";
    char * mount_point = util_alloc_sprintf("%s/%s" , model_config_get_enspath(model_config) , new_case);
    enkf_fs_create_fs(mount_point , BLOCK_FS_DRIVER_ID , NULL , false);

    test_assert_false(enkf_main_case_is_initialized(enkf_main , "does/not/exist" , NULL));
    test_assert_true(enkf_main_case_is_initialized(enkf_main , new_case , NULL));

    enkf_main_free(enkf_main);
    res_config_free(res_config);
  }
  test_work_area_free(work_area);
}



void test_create(const char * config_path, const char * config_file) {
  test_work_area_type * work_area = test_work_area_alloc("enkf_main_create");
  test_work_area_copy_directory_content(work_area, config_path);

  res_config_type * res_config = res_config_alloc_load(config_file);
  enkf_main_type * enkf_main = enkf_main_alloc(res_config, true, true);
  test_assert_true( enkf_main_is_instance( enkf_main ) );

  enkf_main_free( enkf_main );
  res_config_free(res_config);
  test_work_area_free( work_area );
}



int main(int argc , char ** argv) {
  const char * config_path = argv[1];
  const char * config_file = argv[2];
  util_install_signals();
  test_create(config_path, config_file);
  test_case_initialized(config_path, config_file);
  exit(0);
}

