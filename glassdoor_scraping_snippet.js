(function scrape () {
    async function fetchJobDetails(item) {
        return new Promise(resolve => {
            item.click();
            console.log("Clicked " + item.id)
            setTimeout(() => {
                let description = document.querySelector(".JobDetails_jobDescription__uW_fK")?.textContent.trim() || "";
                let company = document.querySelector(".EmployerProfile_employerNameHeading__bXBYr")?.textContent.trim() || "";
                let title = document.querySelector(".heading_Level1__soLZs")?.textContent.trim() || "";
                let age = item.parentElement.parentElement.querySelector(".JobCard_listingAge__jJsuc").textContent.trim() || "";
                let link = item.href;
                console.log("Fetched " + company + " job")
                resolve({ description, company, title, link, age });
            }, 5000);
        });
    }
    
    async function parseContent() {
        let data = [];
        let items = document.querySelectorAll(".JobCard_trackingLink__HMyun");
        console.log("Found " + items.length)
        let count = 0;
        for (let item of items) {
            count = count + 1;
            console.log("Fetching item " + count)
            // if (count >= 5) break;
            let details = await fetchJobDetails(item)
                data.push({...details});
        }
        return data;
    }
    
    function downloadJSON(data, filename) {
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
    
    async function main() {
        const data = await parseContent();
        if (data.length === 0) {
            console.log("No data found. Check your selectors.");
            return;
        }
        downloadJSON(data, "glassdoor_exported_data.json");
    }
    
    main();
})();
