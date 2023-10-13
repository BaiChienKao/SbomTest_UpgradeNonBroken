# This is a sample Python script.

import cgi
import os
import shutil
import sys
import traceback
from typing import List
from http.server import HTTPServer, BaseHTTPRequestHandler

import yaml
from cryptography.hazmat.backends.openssl.backend import Backend
from nvflare.fuel.utils.class_utils import instantiate_class
# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
from nvflare.lighter.spec import Participant, Builder

class Study(object):
    def __init__(self, name: str, description: str, participants: List[Participant]):
        self.name = name
        all_names = list()
        for p in participants:
            if p.name in all_names:
                raise ValueError(f"Unable to add a duplicate name {p.name} into this study.")
            else:
                all_names.append(p.name)
        self.description = description
        self.participants = participants

    def get_participants_by_type(self, type, first_only=True):
        found = list()
        for p in self.participants:
            if p.type == type:
                if first_only:
                    return p
                else:
                    found.append(p)
        return found

class Provisioner(object):
    def __init__(self, root_dir: str, builders:List [Builder]):
        self.root_dir = root_dir
        self.builders = builders
        self.ctx = None

    def _make_dir(self, dirs):
        for dire in dirs:
            if not os.path.exists(dire):
                os.makedirs(dire)

    def _prepare_workspace(self, ctx):
        workspace = ctx.get("workspace")
        wip_dir = os.path.join(workspace, "wip")
        state_dir = os.path.join(workspace, "state")
        resources_dir = os.path.join(workspace, "resources")
        ctx.update(dict(wip_dir=wip_dir, state_dir=state_dir, resources_dir=resources_dir))
        dirs = [workspace, resources_dir, wip_dir, state_dir]
        self._make_dir(dirs)

    def provision(self, study: Study):
        # ctx = {"workspace": os.path.join(self.root_dir, study.name), "study": study}
        workspace = os.path.join(self.root_dir, study.name)
        ctx = {"workspace": workspace}  # study is more static information while ctx is dynamic
        self._prepare_workspace(ctx)
        try:
            for b in self.builders:
                b.initialize(ctx)

            # call builders!
            for b in self.builders:
                b.build(study, ctx)

            for b in self.builders[::-1]:
                b.finalize(ctx)

        except BaseException as ex:
            prod_dir = ctx.get("current_prod_dir")
            if prod_dir:
                shutil.rmtree(prod_dir)
            print("Exception raised during provision.  Incomplete prod_n folder removed.")
            traceback.print_exc()
        finally:
            wip_dir = ctx.get("wip_dir")
            if wip_dir:
                shutil.rmtree(wip_dir)

def customProvisionMain():
    args_custom_folder = "."
    args_workspace = "workspace"
    args_project_file = "project.yml"

    current_path = os.getcwd()
    custom_folder_path = os.path.join(current_path, args_custom_folder)
    sys.path.append(custom_folder_path)
    print("Path list (sys.path) for python codes loading: {}".format(sys.path))
    workspace = args_workspace
    workspace_full_path = os.path.join(current_path, workspace)

    project_file = args_project_file
    project_full_path = os.path.join(current_path, project_file)
    print(f"Project yaml file: {project_full_path}.")

    try:
        project = yaml.safe_load(open(project_full_path, "r"))
    except:
        project = {"api_version":-1}

    api_version = project.get("api_version")
    if api_version not in [2]:
        raise ValueError(f"Incompatible API version found in {project_full_path}")

    study_name = project.get("name")
    study_description = project.get("description", "")
    participants = list()
    for p in project.get("participants"):
        participants.append(Participant(**p))
    study = Study(name=study_name, description=study_description, participants=participants)

    builders = list()
    for b in project.get("builders"):
        path = b.get("path")
        args = b.get("args")
        builders.append(instantiate_class(path, args))

    provisioner = Provisioner(workspace_full_path, builders)

    provisioner.provision(study)

class helloHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path.endswith('/upload'):
            response = """
                    <html><body>
                    <h1></h1></br>
                    <h1>This is the second demo application to build the NVFlare scripts and related files ( such as certificate... ) </h1>
                    <h2>Please upload the yaml configuration file for NVFlare: </h5></br>
                    <form method="POST" enctype="multipart/form-data" action="/BuildResult" >
                    <p>Yaml File: <input name="file" type="file" placeholder="Upload file"></p>
                    <p><input type="submit" value="Upload"></p>
                    </form>
                    </br>
                    <h10>Yaml Example:</h10></br>
                    <h10>_______________________________________________________________________________________________</h10></br>
                    <h10>api_version: 2</h10></br>
                    <h10>name: ExampleProject</h10></br>
                    <h10>description: NVIDIA FLARE sample project yaml file</h10></br>
                    <h10></h10></br>
                    <h10>participants:</h10></br>

                    <h10>&nbsp;&nbsp;- name: example.com</h10></br>
                    <h10>&nbsp;&nbsp;&nbsp;&nbsp;type: server</h10></br>
                    <h10>&nbsp;&nbsp;&nbsp;&nbsp;org: nvidia</h10></br>
                    <h10>&nbsp;&nbsp;&nbsp;&nbsp;fed_learn_port: 8002</h10></br>
                    <h10>&nbsp;&nbsp;&nbsp;&nbsp;admin_port: 8003</h10></br>
                    <h10>&nbsp;&nbsp;&nbsp;&nbsp;# enable_byoc loads python codes in app.  Default is false.</h10></br>
                    <h10>&nbsp;&nbsp;&nbsp;&nbsp;enable_byoc: true</h10></br>
                    <h10>&nbsp;</h10></br>
                    <h10># The same methods in all builders are called in their order defined in builders section</h10></br>
                    <h10>builders:</h10></br>
                    <h10>&nbsp;&nbsp;- path: nvflare.lighter.impl.workspace.WorkspaceBuilder</h10></br>
                    <h10>&nbsp;&nbsp;&nbsp;&nbsp;args:</h10></br>
                    <h10>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;template_file: master_template.yml</h10></br>
                    <h10>_______________________________________________________________________________________________</h10></br>
                    </body></html>
                    """
            self.respond(response)

        else:
            SelfPath = str(self.path)
            FILEPATH = SelfPath.split('/')[-1]
            print('FILEPATH: ' + FILEPATH)

            if os.path.exists(FILEPATH):
                print(FILEPATH + " found, start downloading...")
                with open(FILEPATH, 'rb') as f:
                    print(' open file...')
                    self.send_response(200)
                    self.send_header("Content-Type", 'application/octet-stream')
                    self.send_header("Content-Disposition",
                                     'attachment; filename="{}"'.format(os.path.basename(FILEPATH)))
                    fs = os.fstat(f.fileno())
                    self.send_header("Content-Length", str(fs.st_size))
                    self.end_headers()
                    print('End setting headers: ' + str(self.headers))
                    self.wfile.write(f.read())

            else:
                self.send_response(301)
                self.send_header('content-type', 'text/html')
                self.send_header('Location', '/upload')
                self.end_headers()

    def do_POST(self):
        if self.path.endswith('/BuildResult'):
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST',
                         'CONTENT_TYPE': self.headers['Content-Type'],
                         })
            # print(form)
            filename = form['file'].filename
            data = form['file'].file.read()
            yamlProjectData = "project.yml"  # "Upload/" + filename
            FromFile = open(yamlProjectData, "wb")
            print('start uploading: ' + str(filename))
            FromFile.write(data)
            FromFile.close()
            print('file loaded')

            respondMessage = ""
            BuildSuccess = 0
            projectPath = ''
            projectName = ''
            try:
                customProvisionMain()
                BuildSuccess = 1
                respondMessage = "Result Build successful.\n"

                project_data = yaml.safe_load(open('project.yml', 'r'))
                projectName = project_data.get("name")
                projectPath = "workspace\\" + projectName
                dir_list = os.listdir(projectPath)

                respondMessage = "Result Build successful.\n"
                respondMessage = respondMessage + "Generated result in " + projectPath + " as below:\n"
                for item in dir_list:
                    respondMessage = respondMessage + str(item) + '\n'

            except:
                BuildSuccess = 0
                respondMessage = "Something else went wrong, please upload again.\n"
                print(respondMessage)

            VulnList = '<html><body>\n'
            VulnList += '<h1> Generated items: </h1>\n'
            for line in respondMessage.splitlines():
                VulnList += '<h10>' + line + '</h10>'
                VulnList += '</br>\n'

            if BuildSuccess == 1:
                dir_name = projectPath
                output_filename = projectName
                shutil.make_archive(output_filename, 'zip', dir_name)
                output_filename = projectName + ".zip"

                VulnList += '</br>\n'
                VulnList += '<h10><a href="/' + output_filename + '">' + "Download generated file: " + output_filename + '</a></h10>'
                VulnList += '</br>\n'

            VulnList += '</br>\n'
            VulnList += '<h10><a href="/upload"> Return to upload page. </a></h10>'
            VulnList += '</br>\n'

            VulnList += '</body></html>'

            self.headers['content-length']
            self.respond(VulnList)

    def respond(self, response, status=200):
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-length", len(response))
        self.end_headers()
        self.wfile.write(response.encode())


def main():
    newBackend = Backend()
    print("Backend: " + str(Backend))
    #newSha1 = newBackend.create_hash_ctx(SHA1)
    #print("newSha1: " + str(newSha1) + " , Type: " + str(type(newSha1)))


    PORT = 8000
    server = HTTPServer(("0.0.0.0", PORT), helloHandler)
    print('server running on ' + str(server.server_address)[1:-1])
    server.serve_forever()


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
