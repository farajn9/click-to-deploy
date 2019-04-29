# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
import tempfile
import cloudbuild_k8s_generator


class CloudBuildK8sGeneratorTest(unittest.TestCase):

  def test_path(self):
    cloudbuild = cloudbuild_k8s_generator.CloudBuildConfig(solution='wordpress')
    self.assertEqual(cloudbuild.path, 'k8s/.cloudbuild/wordpress.yaml')

  def test_exists(self):
    with tempfile.NamedTemporaryFile(delete=True) as f:
      cloudbuild = cloudbuild_k8s_generator.CloudBuildConfig(solution='unknown')
      self.assertFalse(cloudbuild.exists())

      cloudbuild.path = f.name
      self.assertTrue(cloudbuild.exists())

  def test_verify(self):
    cloudbuild_config = """
    steps:
    - id: Build unknown
      name: gcr.io/cloud-builders/docker
      dir: k8s
    """
    cloudbuild_template = """
    steps:
    - id: Build {{ solution }}
      name: gcr.io/cloud-builders/docker
      dir: k8s
    """
    with tempfile.NamedTemporaryFile(delete=True) as f:
      f.write(cloudbuild_config)
      f.flush()

      cloudbuild = cloudbuild_k8s_generator.CloudBuildConfig(solution='unknown')
      cloudbuild.path = f.name
      self.assertFalse(cloudbuild.verify())

      cloudbuild.template = cloudbuild_template
      self.assertTrue(cloudbuild.verify())

  def test_generate(self):
    extra_configs = [{
        'name': 'Public service and ingress',
        'env_vars': ['PUBLIC_SERVICE_AND_INGRESS_ENABLED=true']
    }]
    cloudbuild_template = """
    steps:
    - id: Build {{ solution }}
      name: gcr.io/cloud-builders/docker
      dir: k8s

    {%- for extra_config in extra_configs %}

    - id: Verify {{ solution }} ({{ extra_config['name'] }})
      name: gcr.io/cloud-builders/docker
      dir: k8s
      env:
      {%- for env_var in extra_config['env_vars'] %}
      - '{{ env_var }}'
      {%- endfor %}

    {%- endfor %}
    """.strip()

    cloudbuild = cloudbuild_k8s_generator.CloudBuildConfig(solution='wordpress')
    self.assertIsNotNone(cloudbuild.generate())

    cloudbuild = cloudbuild_k8s_generator.CloudBuildConfig(solution='wordpress')
    cloudbuild.extra_configs = []
    self.assertIsNotNone(cloudbuild.generate())

    cloudbuild = cloudbuild_k8s_generator.CloudBuildConfig(solution='wordpress')
    cloudbuild.template = cloudbuild_template
    self.assertEqual(
        cloudbuild.generate(), """
    steps:
    - id: Build wordpress
      name: gcr.io/cloud-builders/docker
      dir: k8s
    """.strip())

    cloudbuild = cloudbuild_k8s_generator.CloudBuildConfig(solution='wordpress')
    cloudbuild.extra_configs = extra_configs
    cloudbuild.template = cloudbuild_template
    self.assertEqual(
        cloudbuild.generate(), """
    steps:
    - id: Build wordpress
      name: gcr.io/cloud-builders/docker
      dir: k8s

    - id: Verify wordpress (Public service and ingress)
      name: gcr.io/cloud-builders/docker
      dir: k8s
      env:
      - 'PUBLIC_SERVICE_AND_INGRESS_ENABLED=true'
    """.strip())

  def test_save(self):
    cloudbuild_config = """
    steps:
    - id: Build unknown
      name: gcr.io/cloud-builders/docker
      dir: k8s
    """
    with tempfile.NamedTemporaryFile(delete=True) as f:
      cloudbuild = cloudbuild_k8s_generator.CloudBuildConfig(
          solution='wordpress')
      cloudbuild.template = cloudbuild_config
      cloudbuild.path = f.name
      cloudbuild.save()
      self.assertEqual(f.read(), cloudbuild_config)

  def test_remove(self):
    with tempfile.NamedTemporaryFile(delete=False) as f:
      cloudbuild = cloudbuild_k8s_generator.CloudBuildConfig(
          solution='wordpress')
      cloudbuild.path = f.name
      cloudbuild.remove()
      self.assertFalse(cloudbuild.exists())


if __name__ == '__main__':
  unittest.main()
