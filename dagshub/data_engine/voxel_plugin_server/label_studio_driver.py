import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Dict, List

import httpx

from dagshub.auth.token_auth import HTTPBearerAuth
from dagshub.common import config

import dagshub.auth


@dataclass
class LabelStudioProject:
    id: int
    branch: str


class LabelStudioDriver:
    def __init__(self):
        self.repo = "KBolashev/MyAwesomeRepo"
        # self.repo = "kirill/DataEngineTesting"
        host = config.host
        token = dagshub.auth.get_token(host=host)
        url = f"{host}/{self.repo}"

        self.auth = ("KBolashev", token)
        self.client = httpx.AsyncClient(base_url=url, timeout=1000.0, auth=self.auth)

    async def run(self):
        await self.start_workspace()
        print(await self.get_all_projects())
        # print(await self.list_projects())
        # projects = await self.list_projects()
        # print(await self.list_storages(1))
        # await self.get_csrf()
        # await self.start_workspace()
        # await self.start_workspace()

    async def get_all_projects(self) -> List[LabelStudioProject]:
        """
        NOTE: this is gonna be slow on big projects
        """
        projects = (await self.list_projects())["results"]

        async def generate_project_entry(list_proj_res: Dict[str, Any]) -> LabelStudioProject:
            id = list_proj_res["id"]
            storage_res = await self.list_storages(id)
            proj = LabelStudioProject(
                id=id,
                branch=storage_res[0]["revision"]
            )
            return proj

        return await asyncio.gather(*(generate_project_entry(p) for p in projects))

    async def list_projects(self) -> Dict[str, Any]:
        resp = await self.client.get("/annotations/api/projects")
        return resp.json()

    async def list_storages(self, project_id: int) -> List[Dict[str, Any]]:
        resp = await self.client.get("/annotations/api/storages/", params={"project": project_id})
        return resp.json()

    async def start_workspace(self):
        await self.send_start_workspace()
        ready_url = "/annotations/ready"
        is_ready = False
        while not is_ready:
            print("Checking labelstudio workspace readiness...")
            resp = await self.client.get(ready_url)
            if resp.status_code == 404:
                # Likely label studio returned it (could be some permission error later)
                # Check that it's label studio actually, it will "Label Studio" in title
                is_ready = b"Label Studio" in resp.content
                assert is_ready
                print("Got status code 404 from Label studio on ready check, workspace is ready")
            elif resp.status_code == 200:
                is_ready = "redirect" in resp.json()

            if not is_ready:
                print(f"Retrying in a bit")
                await asyncio.sleep(5.0)

    async def send_start_workspace(self):
        await self.client.post("annotations/start", data={
            "_csrf": await self.get_csrf()
        })

    async def get_csrf(self):
        if "_csrf" not in self.client.cookies:
            resp = await self.client.get("/")
            assert resp.status_code != 404
            self.client.cookies.update(resp.cookies)
        return self.client.cookies['_csrf']


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    driver = LabelStudioDriver()
    asyncio.run(driver.run())
